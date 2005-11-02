#!/usr/bin/perl

use strict;
use warnings;
use Lingua::GA::Gramadoir;

my $obj = new Lingua::GA::Gramadoir;

# no need to to_lower things, normalize etc. in these
# counts since they're just used for finding dupes, so 
# more uniqueness of tokens in better

sub process_me
{
	(my $text) = @_;
	my %seen;
	$seen{$_}++ foreach (@{$obj->tokenize($text)});
	$text='';
	$text .= "$_ $seen{$_}\n" foreach (sort keys %seen);
	return $text;
}

binmode STDOUT, ":encoding(iso-8859-1)";
binmode STDERR, ":encoding(iso-8859-1)";
binmode STDIN, ":bytes";

my $base='/usr/local/share/crubadan/ga/ciu';
my $range="/snapshot/aimsigh/FREQ";

opendir DIRH, $base or die "could not open $base: $!\n";
foreach my $doctxt (readdir DIRH) {
	next if $doctxt !~ /\.txt$/;
	print "Tokenizing document $doctxt for dupefinder...\n";
	my $sprioc = "$range/$doctxt";
	my $foinse = "$base/$doctxt";
	my $doit = 0;
	if (-e $sprioc) {
		my @stat1 = stat($foinse);
		my @stat2 = stat($sprioc);
		$doit = ($stat1[9] > $stat2[9]);
		print "Tokenizing (out of date)...\n" if $doit;
	}
	else {
		$doit=1;
		print "Tokenizing (first time)...\n";
	}
	if ($doit) {
		open (FOINSE, "<", $foinse) or die "Could not open source file $foinse: $!\n";
		local $/;
		$_ = <FOINSE>;
		close FOINSE;
		open (SPRIOC, ">", $sprioc) or die "Could not open target file $sprioc: $!\n";
		print SPRIOC process_me($_);
		close SPRIOC;
	}
}
closedir DIRH;
exit 0;