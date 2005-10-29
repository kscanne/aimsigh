#!/usr/bin/perl

use strict;
use warnings;
use Lingua::GA::Caighdean;

binmode STDOUT, ":encoding(iso-8859-1)";
binmode STDERR, ":encoding(iso-8859-1)";
binmode STDIN, ":bytes";

my $base='/usr/local/share/crubadan/ga';
my $range='/snapshot/aimsigh/caighdean';
my $caigh = new Lingua::GA::Caighdean(fix_spelling => 0);
my @docIds;

open(MANIFEST, "$base/MANIFEST") || die "Could not open manifest directory: $!\n";
while (<MANIFEST>) {
	if (/^http/) {
		chomp;
		(my $docId) = m/^[^ ]+ ([0-9]+)\.txt$/;
		push @docIds, $docId;
	}
}
close MANIFEST;

my $written=0;
foreach my $docId (@docIds) {
	print "Checking document $docId...\n";
	my $sprioc = "$range/$docId.txt";
	my $foinse = "$base/ciu/$docId.txt";
	my $doit = 0;
	if (-e $sprioc) {
		my @stat1 = stat($foinse);
		my @stat2 = stat($sprioc);
		$doit = ($stat1[9] > $stat2[9]);
		print "Standardizing (out of date)...\n" if $doit;
	}
	else {
		$doit=1;
		print "Standardizing (first time)...\n";
	}
	if ($doit) {
		open (FOINSE, "<", $foinse) or die "Could not open source file $foinse: $!\n";
		local $/;
		$_ = <FOINSE>;
		close FOINSE;
		open (SPRIOC, ">", $sprioc) or die "Could not open target file $sprioc: $!\n";
		print SPRIOC $caigh->caighdean($_);
		close SPRIOC;
		$written++;
#		exit 0 if ($written==25);
	}
}
exit 0;
