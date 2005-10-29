#!/usr/bin/perl

use strict;
use warnings;
# don't bother with PDL, matrices are too big for memory

# hash of all URLs to be ranked; value is the index in the big matrix
my %byurl;
# get crubadan docId (100000..999999) given an index in big matrix
my @docIds;
# store number of links out of page, given index in big matrix
my @linksout;
# array of "sinks" == docs with no links out, stored as index in big matrix
my @sinks;
# array of arrays; $linktome[$i] is an array of indices of docs linking
# to the doc at index $i
my @linktome;

my $base='/usr/local/share/crubadan/ga';
my $q = 0.15;   # Brin-Page damping constant

print "Reading MANIFEST for list of URLs...\n";
open(MANIFEST, "$base/MANIFEST") || die "Could not open manifest directory: $!\n";
while (<MANIFEST>) {
	if (/^http/) {
		chomp;
		(my $url, my $docId) = m/^([^ ]+) ([0-9]+)\.txt$/;
		$byurl{$url}=$.-2;   # 1 is the count on first line of MANIFEST
		push @docIds, $docId;
	}
}
close MANIFEST;

my $N = scalar @docIds;
my $end=$N-1;
my @pr;
push @linktome, [] for (0..$end);
push @pr, 1/$N for (0..$end);   # will be overwritten below

my $htmldocs=0;
my $all=0;
print "Reading cached files, extracting links and computing incidence matrix...\n";
foreach my $docId (@docIds) { 
	open(DOCDATA, "<", "$base/sonrai/$docId.dat") or die "Could not open file $docId.dat: $!\n";
	my $extension;
	my $url;
	my $pre_pr;
	while (<DOCDATA>) {
		chomp;
		if (m/^url: /) {
			$url = $_;
			$url =~ s/^url: //;
		}
		if (m/^format: /) {
			$extension = $_;
			$extension =~ s/^format: //;
		}
		if (m/^pagerank: /) {
			$pre_pr = $_;
			$pre_pr =~ s/^pagerank: //;
		}
	}
	close DOCDATA;
	my $col = $byurl{$url};
	$linksout[$col] = 0;
	$pr[$col] = $pre_pr;
	if ($extension eq 'html') {
		my $realfile="$base/taisce/$docId.$extension";
		$htmldocs++;
		print "$htmldocs... " if ($htmldocs % 100 == 0);
		# note: get_refs returns only uniq refs
		#  also a good good thing: get_refs normalizes all URLs
		#  to the form stored by crubadan, even if the explicit
		#  href in a doc uses something that redirects, etc.
		my @refs = `cat $realfile | /usr/local/bin/get_refs.pl "$url"`;
		foreach my $ref (@refs) {
			chomp $ref;
			if (exists($byurl{$ref})) {
				push @{$linktome[$byurl{$ref}]},$col;
				$linksout[$col]++;
				$all++;
			}
		}
	}
	push(@sinks, $col) if ($linksout[$col]==0);
}
print "Processed $N Irish documents ($htmldocs in HTML); found $all Irish-to-Irish links...\n";

# Now compute page rank
print "Beginning page rank calculation...\n";

for my $iteration (0..2) {
	print "it=$iteration\n";
	my @newpr;
	for my $i (0..$end) {
		print "it=$iteration, row $i of $end\n";
		$newpr[$i]=0;
		for my $j (0..$end) {
			$newpr[$i] += $pr[$j]*$q/$N;
		}
		for my $j (@sinks) {
			$newpr[$i] += $pr[$j]*(1-$q)/$N;
		}
		for my $j (@{$linktome[$i]}) {
			$newpr[$i] += $pr[$j]*(1-$q)/$linksout[$j];
		}
	}
	@pr = @newpr;
	print "pr=(";
	print "$_," foreach (@pr);
	print ")\n";
}

open(SCR, ">", "./scr") or die "Could not open output script: $!\n";
for my $i (0..$end) {
	print SCR "sed -i '/^pagerank/s/.*/$pr[$i]/' $base/sonrai/$docIds[$i].dat";
}
close SCR;

exit 0;
