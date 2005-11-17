#!/usr/bin/perl


open (MAN, "<", "/usr/local/share/crubadan/ga/MANIFEST") or die "Could not open MANIFEST\n";

my %hash;
while (<MAN>) {
	chomp;
	/^([^ ]+) ([0-9]+)\.txt/;
	if (exists($hash{$1})) {
		print "dockill $2\n";
	}
	else {
		$hash{$1} = $2;
	}
}

exit 0;
