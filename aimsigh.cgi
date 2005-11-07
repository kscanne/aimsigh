#!/usr/bin/perl -wT

use strict;
use CGI;
use utf8;
use Encode qw(from_to);
use integer;   # page calcs, "kb" calc

$CGI::DISABLE_UPLOADS = 1;
$CGI::POST_MAX        = 1024;
$ENV{PATH}="/bin:/usr/bin";
delete @ENV{ 'IFS', 'CDPATH', 'ENV', 'BASH_ENV' };

binmode STDOUT, ":utf8";

sub bail_out
{
print '<HTML><META HTTP-EQUIV="REFRESH" CONTENT="0;URL=http://www.aimsigh.com"></HTML>';
exit 0;
}

my @shellargs;
my $q = new CGI;
# http headers, not html headers!
print $q->header(-type=>"text/html", -charset=>'utf-8');

bail_out unless (defined($q->param( "ionchur" )));
my( $ionchur ) = $q->param( "ionchur" ) =~ /^(.+)$/;


bail_out unless (defined($q->param( "claochlu" )));
my ($inneacs) = $q->param( "claochlu" ) =~ /^(NN|YN|YY)$/;

# this variable not guaranteed to appear
my $feicthe=0;
if (defined($q->param( "feicthe" ))) {
	($feicthe) = $q->param( "feicthe" ) =~ /^([0-9]+)$/;
}
# else just leave it as 0

if (defined($q->param( "neamhchaighdean" )) and $q->param( "neamhchaighdean" ) =~ m/./) {
	$inneacs .= 'Y';
}
else {
	$inneacs .= 'N';
}

bail_out unless ( $ionchur );

$ionchur =~ s/'/\'/g;

############################################################################
#  End of CGI stuff; rest of code is for sending query to cuard,
#  and then generating HTML from the results

my $cgi='http://borel.slu.edu/cgi-bin/aimsigh.cgi';
my $crub='/usr/local/share/crubadan/ga';
my $snapshot='/snapshot/aimsigh';

# There are three command line args:
# First is the query itself, from the search box:
my $qhtml = $ionchur;
from_to($qhtml,"UTF-8","ISO-8859-1");  # double-encoded, so really the result is utf-8 encoded
my $flattened = $qhtml;
#  convert to big OR of regexen
my $patt = qr/$flattened/;

# takes a docId number, reads the tokenized file from YNN, NNY, as appropriate,
# finds first search term it can, records this line number, then extracts
# the same line number out of the NNN file
sub bain_sliocht_as
{
	(my $docId) = @_;
	my $sliocht='Gan sliocht';
	my $line=-1;
	open(SONRAI, "<", "$snapshot/$inneacs/$docId.txt") or die "Could not open tokenized file $inneacs/$docId.txt: $!\n";
	while (<SONRAI>) {
		if (/$patt/i) {
			chomp;
			$sliocht=$_;
			$line=$.;
			last;
		}
	}
	close SONRAI;
	if ($inneacs ne 'NNN') {
		open(CLEAN, "<", "$snapshot/NNN/$docId.txt") or die "Could not open tokenized file NNN/$docId.txt: $!\n";
		while (<CLEAN>) {
			if ($. == $line) {
				chomp;
				$sliocht=$_;
				last;
			}
		}
		close CLEAN;
	}
	#  now clean it up
	$sliocht =~ s/----+/---/g;
	if (length($sliocht) > 300) {
		$sliocht = substr($sliocht,0,296)."...";
	}

	return $sliocht;
}

# generate a chunk of HTML for one given "hit"
sub cruthaigh_toradh
{
	(my $docId) = @_;
	my $sliocht = bain_sliocht_as($docId);
	open(SONRAI, "<", "$crub/sonrai/$docId.dat") or die "Could not open data file $docId: $!\n";
	my %hash;
	while (<SONRAI>) {
		chomp;
		m/^([^:]+): (.*)$/;	
		$hash{$1} = $2;
	}
	if (length($hash{'title'}) > 100) {
		$hash{'title'} = substr($hash{'title'},0,96)."...";
	}
	$hash{'size'} = 1+$hash{'size'}/1024;
	print "[".$hash{'format'}."]&nbsp;" unless ($hash{'format'} eq 'html');
	print "<span class=\"mor\"><a href=\"".$hash{'url'}."\">".$hash{'title'}."</a></span><br>\n";
	print "<span class=\"beag\">$sliocht</span><br>\n";
	$hash{'url'} =~ s/^[a-z]+:\/\///;
	print "<span class=\"uainebeag\">".$hash{'url'}." - ".$hash{'size'}."k -</span> <span class=\"beag\"><a href=\"http://borel.slu.edu/\">I dTaisce</a></span><br><br>";
}

#######################################################################
#     Start of main program - call search engine to get candidate docs
#######################################################################

local *PIPE;

my $pid = open PIPE, "-|";
die "Theip ar dhéanamh an fhorc: $!" unless defined $pid;
unless ( $pid ) {
	exec '/usr/local/bin/cuard', $ionchur, 'TEIDIL' or die "Ní féidir píopa a oscailt: $!\n";
}
my %match_hash;
my @matches;
# "cuard" returns the number of hits, and then a list of corpus
# filenames 100000..999999 one per line
my $iomlan = <PIPE>;   # number of title hits; ignorable
while (<PIPE>) {
	chomp;
	$match_hash{$_}++;
	push @matches, $_;
}
close PIPE;


my $pid2 = open PIPE, "-|";
die "Theip ar dhéanamh an fhorc: $!" unless defined $pid2;
unless ( $pid2 ) {
	exec '/usr/local/bin/cuard', $ionchur, $inneacs or die "Ní féidir píopa a oscailt: $!\n";
}
$iomlan = <PIPE>;   # number of hits for reporting
while (<PIPE>) {
	chomp;
	push @matches, $_ unless (exists($match_hash{$_}));
}
close PIPE;

#######################################################################
my $num = scalar @matches;
my $start = $feicthe + 1;
my $end = $feicthe + 10;  # ten results per page
$end = $num if ($num < $end);
my $lastpagetotal = 1 + ($num-1)/10;

# Finally, output first page of HTML
my $neamhfoirm='';
my $neamh='';
if ($inneacs =~ /Y$/) {
	$neamhfoirm='<input type="hidden" name="neamhchaighdean" value="neamhchaighdean">';
	$neamh='&neamhchaighdean';
}
(my $claoch) = $inneacs =~ m/^(..)(.)$/;
print <<HEADER;
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN"
        "http://www.w3.org/TR/html4/strict.dtd">
<html lang="ga">
  <head>
    <title>$qhtml - Cuardach aimsigh.com</title>
    <meta http-equiv="Content-Language" content="ga">
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
    <meta name="author" content="aimsigh.com">
    <link rel="stylesheet" href="/aimsigh/aimsigh.css" type="text/css">
    <link rel="shortcut icon" href="/aimsigh/favicon.ico" type="image/x-icon">
  </head>
  <body>
    <form class="laraithe" action="/cgi-bin/aimsigh.cgi" method="POST">
      <a href="http://www.aimsigh.com/"><img class="nasctha" src="/aimsigh/aimsigh.png" alt="aimsigh.com"></a><br>
      <input size="50" name="ionchur" value="$qhtml"><br>
      <input type="submit" name="foirm" value="Aimsigh é"><br>
      <input type="hidden" name="feicthe" value="0">
      <input type="hidden" name="claochlu" value="$claoch">
      $neamhfoirm
    </form>
    <hr>
HEADER


if ($num == 0) {
	print "Níor aimsíodh d'iarratas i gcáipéis ar bith.<br><br>\n";
}
else {
	print "<b>Tagairtí $start - $end as ";
#	print "níos mó ná " if ($iomlan == 20000);  # zettair-specific
	print "$iomlan á dtaispeáint:</b><br>\n";

	cruthaigh_toradh($matches[$_-1]) for ($start..$end);

	unless ($lastpagetotal == 1) {
		my $currpage = 1 + $feicthe/10;
		my $firstlinkedpage = $currpage-10;
		$firstlinkedpage = 1 if ($firstlinkedpage < 1);
		my $lastlinkedpage = $currpage+9;
		$lastlinkedpage = $lastpagetotal if ($lastlinkedpage > $lastpagetotal);
		my $newseen;
		print "<p class=\"laraithe\"><b>Leathanach:</b>&nbsp;&nbsp;&nbsp;&nbsp;\n";
		if ($firstlinkedpage > 1) {
			$newseen=$feicthe-10;
			print "<a href=\"$cgi?ionchur=$ionchur&feicthe=$newseen&claochlu=$claoch$neamh\"><b>Siar</b></a>\n";
		}
		for my $leathanach ($firstlinkedpage..$lastlinkedpage) {
			if ($leathanach == $currpage) {
				print "<b>$leathanach</b>\n";
			}
			else {
				$newseen=10*($leathanach-1);
				print "<a href=\"$cgi?ionchur=$ionchur&feicthe=$newseen&claochlu=$claoch$neamh\">$leathanach</a>\n";
			}
		}
		$newseen=$feicthe+10;
		if ($currpage < $lastpagetotal) {
			print "<a href=\"$cgi?ionchur=$ionchur&feicthe=$newseen&claochlu=$claoch$neamh\"><b>Ar Aghaidh</b></a>\n";
		}
		print "</p>\n";
	}  # if more than one page
}  # if at least one hit


print <<FOOTER;
    <hr>
    <p class="anbheag">Cóipcheart © 2005 <a href="/index.html">Kevin P. Scannell</a>. Gach ceart ar cosnamh.<br>Déan teagmháil linn ag <a href="mailto:eolas\@aimsigh.com">eolas\@aimsigh.com</a>.</p>
  </body>
</html>
FOOTER

exit 0;
