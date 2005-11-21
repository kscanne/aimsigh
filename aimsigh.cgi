#!/usr/bin/speedy -wT

use strict;
use CGI;
use utf8;
use Encode qw(decode encode);
use SWISH::API;
use integer;   # page calcs, "kb" calc
use Lingua::GA::Stemmer;
use Lingua::GA::Caighdean;

# persistent globals
use vars qw($gramadoir_stemmer);
unless (defined($gramadoir_stemmer)) {
	$gramadoir_stemmer = new Lingua::GA::Stemmer;
}

sub bail_out
{
	print '<HTML><META HTTP-EQUIV="REFRESH" CONTENT="0;URL=http://www.aimsigh.com"></HTML>';
	exit 0;
}

# prepare query for inclusion as postdata
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

# inverse of previous; call right when ionchur is read from CGI
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

# translate aimsigh.com query syntax to underlying search engine's syntax
sub aimsigh_to_engine
{
	(my $str) = @_;
	$str =~ s/([ ()"])[Aa][Nn][Dd]([ ()"])/$1 "and" $2/g;
	$str =~ s/([ ()"])[Oo][Rr]([ ()"])/$1 "or" $2/g;
	$str =~ s/([ ()"])[Nn][Oo][Tt]([ ()"])/$1 "not" $2/g;
	$str =~ s/([ )])AGUS([( ])/$1AND$2/g;
	$str =~ s/([ )])NÓ([( ])/$1OR$2/g;
	$str =~ s/([ ()"])GAN([( ])/$1NOT$2/g;
	$str =~ s/^GAN([( ])/NOT$2/g;
	return $str;
}

# normalize just one term
sub normalize_term
{
	(my $str, my $index) = @_;
	return $str if ($str eq 'AND' or $str eq 'OR' or $str eq 'NOT');
	if ($index =~ m/^YY/) {
		my $s = $gramadoir_stemmer->stem($str);
		$s =~ m/<[A-Z][^>]*>([^<]+)<\/[A-Z]>/;  # should be full str!
		$str = $gramadoir_stemmer->strip_mutation(
		       $gramadoir_stemmer->tolower($1));
	}
	else {
		$str = $gramadoir_stemmer->tolower($str);
		$str = $gramadoir_stemmer->strip_mutation($str) if ($index =~ m/^Y/);
	}
	return $str;
}

# called after aimsigh_to_engine; convert all search terms to 
# the normalized form appropriate for the desired index (NNN, YNN, etc.)
sub normalize_terms
{
	(my $str, my $index) = @_;
	if ($index =~ m/Y$/) {
		my $gr = new Lingua::GA::Caighdean(fix_spelling => 0);
		$str = $gr->caighdean($str); # preserves AND, NOT, quotes, etc.
	}
	$str =~ s/([^ ()"]+)/normalize_term($1,$index)/eg;
	return $str;
}

# see "loosen" below
sub partner
{
	(my $str) = @_;
	$str =~ s/^(.).*/$1/;
	$str =~ tr/a-zA-ZàáâãäåæçèéêëìíîïðñòóôõöøùúûüýþÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖØÙÚÛÜÝÞ/A-Za-zÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖØÙÚÛÜÝÞàáâãäåæçèéêëìíîïðñòóôõöøùúûüýþ/;
	return $str;
}

# used in creating regex for post-retrieval scan
sub loosen
{
	(my $str) = @_;
	$str =~ s/ /./g;
	$str =~ s/([^.'-])/"[$1".partner("$1")."]"/eg;
	return $str;
}

#  Set up regex for finding sliocht in post-retrieval scan of tokenized file
#  Since we search in YNN, YYN, etc. it is important to build this out
#  of the *normalized* query!
sub create_flattened {

	(my $hackable) = @_;

	my $wordchar='0-9a-zA-ZàáâãäåæçèéêëìíîïðñòóôõöøùúûüýþÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖØÙÚÛÜÝÞ';
	my $flattened = "(^|[^$wordchar])(";
	$flattened .= loosen($1)."|" while ($hackable =~ m/"([^"]+)"/g);
	$hackable =~ s/"[^"]+"/ /g;
	while ($hackable =~ m/([^ ()"]+)/g) {
		my $tearma = $1;
		$tearma =~ s/^['-]+//;
		$tearma =~ s/['-]+$//;
		$flattened .= loosen($tearma)."|" unless ( $tearma eq '' or 
							$tearma eq 'AND' or
							$tearma eq 'OR' or
							$tearma eq 'NOT' );
	}
	$flattened =~ s/\|$//;
	$flattened .= ")([^$wordchar]".'|$)';
	my $patt = qr/$flattened/;

	return $patt;
}

# takes a docId number, reads the tokenized file from YNN, NNY, as appropriate,
# finds first search term it can, records this line number, then extracts
# the same line number out of the ABAIRT file
sub bain_sliocht_as
{
	(my $docId, my $patrun, my $inneacs) = @_;
	my $sliocht='Gan sliocht';
	my $line=-1;
	open(SONRAI, "<", "/snapshot/aimsigh/$inneacs/$docId.txt") or die "Could not open tokenized file $inneacs/$docId.txt: $!\n";
	while (<SONRAI>) {
		if (/$patrun/) {
			chomp;
			$sliocht=$_;
			$line=$.;
			last;
		}
	}
	close SONRAI;
	open(CLEAN, "<", "/snapshot/aimsigh/ABAIRT/$docId.txt") or die "Could not open clean file ABAIRT/$docId.txt: $!\n";
	while (<CLEAN>) {
		if ($. == $line) {
			chomp;
			$sliocht=$_;
			last;
		}
	}
	close CLEAN;
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
	(my $docId, my $patrun, my $inneacs) = @_;
	my $sliocht = bain_sliocht_as($docId, $patrun, $inneacs);
	open(SONRAI, "<", "/usr/local/share/crubadan/ga/sonrai/$docId.dat") or die "Could not open data file $docId: $!\n";
	my %hash;
	while (<SONRAI>) {
		chomp;
		m/^([^:]+): (.*)$/;	
		$hash{$1} = $2;
	}
	close SONRAI;
	if (length($hash{'title'}) > 100) {
		$hash{'title'} = substr($hash{'title'},0,96)."...";
	}
	$hash{'size'} = 1+$hash{'size'}/1024;
	print "<!--m-->";
	print "[".$hash{'format'}."]&nbsp;" unless ($hash{'format'} eq 'html');
	print "<span class=\"mor\"><a href=\"".$hash{'url'}."\">".$hash{'title'}."</a></span><br>\n";
	print "<span class=\"beag\">$sliocht</span><br>\n";
	$hash{'url'} =~ s/^[a-z]+:\/\///;
	print "<span class=\"uainebeag\">".$hash{'url'}." - ".$hash{'size'}."k -</span> <span class=\"beag\"><a href=\"http://borel.slu.edu/\">I&nbsp;dTaisce</a></span><br><br><!--n-->\n";
}

#######################################################################
#     Start of main program - call search engine to get candidate docs
#######################################################################

sub cuardach {
	(my $query, my $cineal, my $href) = @_;

	my $sw = SWISH::API->new( "/home/kps/seal/inneacs/$cineal.index" );
	$sw->AbortLastError if $sw->Error;

	my $results = $sw->Query( $query );
	my $count = 0;

	# ranking parameters:
	  # in case doc is not among 1st 1000 in inneacs search, don't
	  # punish it with a 0 relevance...
	my $baserelevance=250;
	  # divide page ranking (0..numdocs-1) by this number
	my $pagerankdamp=1;
	  # add this number if search terms appear in title
	my $titlebonus=100000/$pagerankdamp;

	while ( my $result = $results->NextResult ) {
		my $title=$result->Property( "swishdocpath" );
		$title =~ /^([0-9]+)-([0-9]+)$/;
		if ($cineal eq 'TEIDIL') {
			$href->{$2}=$baserelevance - ($1-100000)/$pagerankdamp unless (exists($href->{$2}));
			$href->{$2}+=$titlebonus;
		}
		else {
			$href->{$2}=$result->Property( "swishrank" ) - ($1-100000)/$pagerankdamp;
		}
		$count++;
		last if ($count==500);
	}
	return $results->Hits;
}

sub generate_html_header {

	( my $inneacs, my $pristine ) = @_;

	my $neamhfoirm='';
	$neamhfoirm='<input type="hidden" name="neamhchaighdean" value="neamhchaighdean">' if ($inneacs =~ /Y$/);
	(my $claoch) = $inneacs =~ m/^(..)(.)$/;

	# should probably also do > ASCII chars as 
	# &#XXXX; though FF and IE seem ok with them
	# for use in URLs (succeeding pages linked at bottom of results page)
	$pristine =~ s/"/&quot;/g;
	print <<HEADER;
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN"
        "http://www.w3.org/TR/html4/strict.dtd">
<html lang="ga">
  <head>
    <title>$pristine - Cuardach aimsigh.com</title>
    <meta http-equiv="Content-Language" content="ga">
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
    <meta name="author" content="aimsigh.com">
    <link rel="stylesheet" href="/aimsigh/aimsigh.css" type="text/css">
    <link rel="shortcut icon" href="/aimsigh/favicon.ico" type="image/x-icon">
  </head>
  <body>
HEADER
#    <form class="laraithe" action="/cgi-bin/aimsigh.cgi" method="POST">
#      <a href="http://www.aimsigh.com/"><img class="nasctha" src="/aimsigh/aimsigh.png" alt="aimsigh.com"></a><br>
#      <input size="50" name="ionchur" value="$pristine"><br>
#      <input type="submit" name="foirm" value="Aimsigh é"><br>
#      <input type="hidden" name="feicthe" value="0">
#      <input type="hidden" name="claochlu" value="$claoch">
#      $neamhfoirm
#    </form>
#    <hr>
}

sub generate_html_footer {
	print <<FOOTER;
    <hr>
    <p class="anbheag">Cóipcheart © 2005 <a href="http://borel.slu.edu/index.html">Kevin P. Scannell</a>. Gach ceart ar cosnamh.<br>Déan teagmháil linn ag <a href="mailto:eolas\@aimsigh.com">eolas\@aimsigh.com</a>.</p>
  </body>
</html>
FOOTER
}

sub generate_html_output {

	(my $matchesref, my $hitz, my $feicthe, my $inneacs, my $postdata, my $ionchur) = @_;

	my $num = scalar(@$matchesref);
	if ($num == 0) {
		print "Níor aimsíodh d'iarratas i gcáipéis ar bith.<br><br>\n";
	}
	else {
		$num = 500 if ($num > 500); # might happen...
		my $start = $feicthe + 1;
		my $end = $feicthe + 10;    # ten results per page
		$end = $num if ($num < $end);
		my $lastpagetotal = 1 + ($num-1)/10;

		my $neamh='';
		$neamh='&neamhchaighdean' if ($inneacs =~ /Y$/);
		(my $claoch) = $inneacs =~ m/^(..)(.)$/;
		$hitz = $num if ($num > $hitz);    # shouldn't happen...
		print "<b>Cáipéisí $start - $end as $hitz á dtaispeáint:</b><br><!--a-->\n";
	
		my $patrun = create_flattened($ionchur);
		cruthaigh_toradh($matchesref->[$_-1], $patrun, $inneacs) for ($start..$end);

		unless ($lastpagetotal == 1) {
			my $currpage = 1 + $feicthe/10;
			my $firstlinkedpage = $currpage-10;
			$firstlinkedpage = 1 if ($firstlinkedpage < 1);
			my $lastlinkedpage = $currpage+9;
			$lastlinkedpage = $lastpagetotal if ($lastlinkedpage > $lastpagetotal);
			my $newseen;
			print "<!--z--><p class=\"laraithe\"><b>Leathanach:</b>&nbsp;&nbsp;&nbsp;&nbsp;\n";
			my $cgi='http://borel.slu.edu/cgi-bin/aimsigh.cgi';
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
}  # end generate_html  subroutine


sub get_cgi_data {

	$CGI::DISABLE_UPLOADS = 1;
	$CGI::POST_MAX        = 1024;
	$ENV{PATH}="/bin:/usr/bin";
	delete @ENV{ 'IFS', 'CDPATH', 'ENV', 'BASH_ENV' };

	my $q = new CGI;
	# http headers, not html headers!  needed before first "bail_out"
	print $q->header(-type=>"text/html", -charset=>'utf-8');

	bail_out unless (defined($q->param( "ionchur" )));
	my( $ionchur ) = $q->param( "ionchur" ) =~ /^(.+)$/;
	$ionchur = decode("UTF-8", $ionchur);  # utf-8 from CGI, convert to perl string
	$ionchur = decode_URL($ionchur);   # if inputs were post data

	# important in particular to kill chars that are special to 
	# swish-e search that we don't want to support: *,= esp.
	# also stuff like shell metachars for safety (even though we're now
	# not using any external programs!)   ISO-8859-1 ONLY!
	$ionchur =~ s/[^0-9a-zA-ZàáâãäåæçèéêëìíîïðñòóôõöøùúûüýþÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖØÙÚÛÜÝÞ ()"'-]/ /g;

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

	return ($ionchur, $inneacs, $feicthe);
}

sub priomh {
	# key to guarantee that each (latin-1) sliocht is written to html doc in utf8
	binmode STDOUT, ":utf8";

	(my $ionchur, my $inneacs, my $feicthe) = get_cgi_data();

	# now before converting query to swish-e syntax, need to store
	# it as-is for the results page:
	# used for "value" in form at top of results page
	# and also for title of results page; also it gets
	# encoded and used as the "postdata" in the URL
	my $pristine = $ionchur;

	$ionchur = aimsigh_to_engine($ionchur);
	$ionchur = normalize_terms($ionchur, $inneacs);

	bail_out unless ( $ionchur );   # or better if no search terms?
	$ionchur =~ s/'/\'/g;

	open (FUN, ">>", "/home/httpd/aimsigh.log") or die "Could not open aimsigh log: $!\n";
	print FUN "NORMALIZED SEARCH: $ionchur\n";
	close FUN;

	my %match_hash;
	#  this translation is guaranteed to work because of filters applied to
	#  the ionchur string above...
	my $topipe = encode("ISO-8859-1", $ionchur);
	my $iomlan = cuardach($topipe, $inneacs, \%match_hash);
	cuardach($topipe, 'TEIDIL', \%match_hash);  # ignore return
	my @matches = (sort {$match_hash{$b} <=> $match_hash{$a}} keys %match_hash);
	generate_html_header($inneacs, $pristine);
	generate_html_output(\@matches, $iomlan, $feicthe,
				$inneacs, encode_URL($pristine),$ionchur);
	generate_html_footer();

}

priomh();
exit 0;
