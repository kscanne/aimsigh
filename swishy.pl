#!/usr/bin/perl

use strict;
use warnings;

# reads a list of docId's on stdin that have been sorted by PageRank
my $base="/snapshot/aimsigh/$ARGV[0]";
my $count=100000;
while (<STDIN>) {
	chomp;
	my $docId=$_;
	open (FOINSE, "<", "$base/$docId.txt") or die "Could not open $docId: $!\n";
	my $dum=<FOINSE>;   # <DOC>
	$dum=<FOINSE>;      # <DOCNO>...
	my $doc='';
	while (<FOINSE>) {
		$doc .= $_ unless /^<\/DOC>$/;
	}
	my $size = length $doc;
	print "Path-Name: $count-$docId\n";
	print "Content-Length: $size\n";
	print "Document-Type: TXT*\n";
	print "\n";
	print $doc;
	$count++;
}
exit 0;
