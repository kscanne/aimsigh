#!/usr/bin/perl

# computes tfidf weightings for all terms in all files
# and writes them in the TFIDF directory -- see Jurafsky-Martin p.653

use strict;
use warnings;

binmode STDOUT, ":encoding(iso-8859-1)";
binmode STDERR, ":encoding(iso-8859-1)";
binmode STDIN, ":bytes";

my $base='/snapshot/aimsigh/NNN';
my %bighash;
my $N;

opendir DIRH, $base or die "could not open $base: $!\n";
foreach my $doctxt (readdir DIRH) {
	next if $doctxt !~ /\.txt$/;
	$N++;
	print "$N..." if ($N % 100 == 0);
	open (FOINSE, "<", "$base/$doctxt") or die "Could not open source file $doctxt: $!\n";
	while (<FOINSE>) {
		chomp;
		s/ .*//;
		$bighash{$_}++;
	}
	close FOINSE;
}
closedir DIRH;
print "Done reading token files; computing logs...\n";
foreach (keys %bighash) {
	$bighash{$_} = log($N/$bighash{$_});
}
#open(OUTPUT, ">", "/snapshot/aimsigh/IDF.txt") or die "could not open output file: $!\n";
#print OUTPUT "$bighash{$_} $_\n" foreach (sort {$bighash{$b} <=> $bighash{$a}} keys %bighash);
#close OUTPUT;
$N=0;
my $range = '/snapshot/aimsigh/TFIDF';
print "Now rereading token files and computing tfidf...\n";
opendir DIRH, $base or die "could not open $base: $!\n";
foreach my $doctxt (readdir DIRH) {
	my %lilhash;
	next if $doctxt !~ /\.txt$/;
	my $foinse = "$base/$doctxt";
	my $sprioc = "$range/$doctxt";
	$N++;
	print "$N..." if ($N % 100 == 0);
	my $doit = 0;
	if (-e $sprioc) {
		my @stat1 = stat($foinse);
		my @stat2 = stat($sprioc);
		$doit = ($stat1[9] > $stat2[9]);
		print "Computing tfidf for $doctxt (out of date)...\n" if $doit;
	}
	else {
		$doit = 1;
		print "Computing tfidf for $doctxt (first time)...\n";
	}
	if ($doit) {
		open (FOINSE, "<", $foinse) or die "Could not open source file $doctxt: $!\n";
		my $len = 0;
		while (<FOINSE>) {
			chomp;
			(my $w, my $freq) = /^([^ ]+) ([0-9]+)$/;
			my $temp = $freq*$bighash{$w};
			$lilhash{$w} = $temp;
			$len += ($temp*$temp);
		}
		close FOINSE;
		$len = sqrt($len);
		$lilhash{$_} /= $len foreach (keys %lilhash);

		open(OUTPUT, ">", $sprioc) or die "could not open output file in TFIDF: $!\n";
		print OUTPUT "$lilhash{$_} $_\n" foreach (sort {$lilhash{$b} <=> $lilhash{$a}} keys %lilhash);
		close OUTPUT;
	}
}
closedir DIRH;

exit 0;
