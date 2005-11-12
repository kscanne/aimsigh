#!/usr/bin/perl -wT

use strict;
use CGI;
use utf8;
use Encode qw(from_to decode encode);
use SWISH::API;
use integer;   # page calcs, "kb" calc

$CGI::DISABLE_UPLOADS = 1;
$CGI::POST_MAX        = 1024;
$ENV{PATH}="/bin:/usr/bin";
delete @ENV{ 'IFS', 'CDPATH', 'ENV', 'BASH_ENV' };

# key to guarantee that each (latin-1) sliocht is written to html doc in utf8
binmode STDOUT, ":utf8";

sub bail_out
{
print '<HTML><META HTTP-EQUIV="REFRESH" CONTENT="0;URL=http://www.aimsigh.com"></HTML>';
exit 0;
}

sub encode_URL
{
	(my $str) = @_;
	$str =~ s/ /+/g;
	$str =~ s/"/%22/g;
	$str =~ s/'/%27/g;
	$str =~ s/\(/%28/g;
	$str =~ s/\)/%29/g;
	return $str;
}

sub decode_URL
{
	(my $str) = @_;
	$str =~ s/\+/ /g;   # not really necessary since this is the default
	$str =~ s/%22/"/g;
	$str =~ s/%27/'/g;
	$str =~ s/%28/(/g;
	$str =~ s/%29/)/g;
	return $str;
}

my @shellargs;
my $q = new CGI;
# http headers, not html headers!
print $q->header(-type=>"text/html", -charset=>'utf-8');

bail_out unless (defined($q->param( "ionchur" )));
my( $ionchur ) = $q->param( "ionchur" ) =~ /^(.+)$/;
$ionchur = decode("UTF-8", $ionchur);  # utf-8 from CGI, convert to perl string
$ionchur = decode_URL($ionchur);
my $pristine = $ionchur;   # used for "value" in form at top of results page
$pristine =~ s/"/&quot;/g; # value is quoted so encode any literal quotes

# important in particular to kill chars that are special to 
# swish-e search that we don't want to support: *,= esp.
# also stuff like shell metachars for safety (even though we're now
# not using any external programs!)   ISO-8859-1 ONLY!
$ionchur =~ s/[^0-9a-zA-ZàáâãäåæçèéêëìíîïðñòóôõöøùúûüýþÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖØÙÚÛÜÝÞ ()"'-]/ /g;
#  translate aimsigh search syntax to swish-e
$ionchur =~ s/([ ()"])[Aa][Nn][Dd]([ ()"])/$1 "and" $2/g;
$ionchur =~ s/([ ()"])[Oo][Rr]([ ()"])/$1 "or" $2/g;
$ionchur =~ s/([ ()"])[Nn][Oo][Tt]([ ()"])/$1 "not" $2/g;
$ionchur =~ s/([ )])AGUS([( ])/$1AND$2/g;
$ionchur =~ s/([ )])NÓ([( ])/$1OR$2/g;
$ionchur =~ s/([ ()"])GAN([( ])/$1NOT$2/g;
$ionchur =~ s/^GAN([( ])/NOT$2/g;

bail_out unless ( $ionchur );
$ionchur =~ s/'/\'/g;


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


############################################################################
#  End of CGI stuff; rest of code is for sending query to swish-e,
#  and then generating HTML from the results

my $cgi='http://borel.slu.edu/cgi-bin/aimsigh.cgi';
my $crub='/usr/local/share/crubadan/ga';
my $snapshot='/snapshot/aimsigh';

# some useful alternate versions of the query:
my $qhtml = $ionchur;   # for results page title; should convert to entities (&#UTF; easiest?, include &quot; !)
# for use in URLs (succeeding pages linked at bottom of results page)
my $postdata = encode_URL($ionchur);
#  for finding sliocht in post-retrieval scan of tokenized file
my $flattened = $ionchur;
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

sub cuardach {
	(my $query, my $cineal, my $href, my $aref) = @_;

	my $sw = SWISH::API->new( "/home/kps/seal/inneacs/$cineal.index" );
	$sw->AbortLastError if $sw->Error;

	open (FUN, ">>", "/home/httpd/aimsigh.log") or die "Could not open aimsigh log: $!\n";
	print FUN "Q=$query\nC=$cineal\n\n";
	close FUN;

	my $results = $sw->Query( $query );
	my %hits;
	my $count = 0;

	while ( my $result = $results->NextResult ) {
		my $title=$result->Property( "swishdocpath" );
		$title =~ /^([0-9]+)-([0-9]+)$/;
		$hits{$2}=$1;
		$count++;
		last if ($count==500);
	}

	if ($cineal eq 'TEIDIL') {
		foreach (sort {$hits{$a} <=> $hits{$b}} keys %hits) {
			$href->{$_}++;
			push @$aref, $_;
		}
	}
	else {
		foreach (sort {$hits{$a} <=> $hits{$b}} keys %hits) {
			push @$aref, $_ unless (exists($href->{$_}));
		}
	}
	return $results->Hits;
}


my %match_hash;
my @matches;
#  this translation is guaranteed to work because of filters applied to
#  the ionchur string above...
my $topipe = encode("ISO-8859-1", $ionchur);
cuardach($topipe, 'TEIDIL', \%match_hash, \@matches);  # ignore return
my $iomlan = cuardach($topipe, $inneacs, \%match_hash, \@matches);
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
      <input size="50" name="ionchur" value="$pristine"><br>
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
			print "<a href=\"$cgi?ionchur=$postdata&feicthe=$newseen&claochlu=$claoch$neamh\"><b>Siar</b></a>\n";
		}
		for my $leathanach ($firstlinkedpage..$lastlinkedpage) {
			if ($leathanach == $currpage) {
				print "<b>$leathanach</b>\n";
			}
			else {
				$newseen=10*($leathanach-1);
				print "<a href=\"$cgi?ionchur=$postdata&feicthe=$newseen&claochlu=$claoch$neamh\">$leathanach</a>\n";
			}
		}
		$newseen=$feicthe+10;
		if ($currpage < $lastpagetotal) {
			print "<a href=\"$cgi?ionchur=$postdata&feicthe=$newseen&claochlu=$claoch$neamh\"><b>Ar Aghaidh</b></a>\n";
		}
		print "</p>\n";
	}  # if more than one page
}  # if at least one hit


print <<FOOTER;
    <hr>
    <p class="anbheag">Cóipcheart © 2005 <a href="http://borel.slu.edu/index.html">Kevin P. Scannell</a>. Gach ceart ar cosnamh.<br>Déan teagmháil linn ag <a href="mailto:eolas\@aimsigh.com">eolas\@aimsigh.com</a>.</p>
  </body>
</html>
FOOTER

exit 0;
