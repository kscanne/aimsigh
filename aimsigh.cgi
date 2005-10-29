#!/usr/bin/perl -wT

use strict;
use CGI;
use utf8;

$CGI::DISABLE_UPLOADS = 1;
$CGI::POST_MAX        = 1024;

$ENV{PATH}="/bin:/usr/bin";
delete @ENV{ 'IFS', 'CDPATH', 'ENV', 'BASH_ENV' };

my $SEARCHENGINE = '/usr/local/bin/aimsigh';
my @shellargs;
my $q = new CGI;
my( $ionchur ) = $q->param( "ionchur" ) =~ /^(.+)$/;
my $inneacs='';
my $feicthe=0;

if (defined($q->param( "claochlu" ))) {
	($inneacs) = $q->param( "claochlu" ) =~ /^(NN|YN|YY)$/;
}
else {
	die "Unselected radio button in aimsigh.cgi\n";
}

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

local *PIPE;

# http headers, not html headers!
print $q->header(-type=>"text/html", -charset=>'utf-8');

unless ( $ionchur ) {
print '<HTML><META HTTP-EQUIV="REFRESH" CONTENT="0;URL=http://www.aimsigh.com"></HTML>';
exit 0;
}

$ionchur =~ s/'/\'/g;

my $pid = open PIPE, "-|";
die "Theip ar dhéanamh an fhorc: $!" unless defined $pid;
unless ( $pid ) {
	     exec $SEARCHENGINE, ($ionchur, $inneacs, $feicthe) or die "Ní féidir píopa a oscailt: $!";
	}

print while <PIPE>;
close PIPE;
exit 0;
