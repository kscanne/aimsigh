
SHELL=/bin/sh
MAKE=/usr/bin/make
INSTALL=/usr/bin/install
INSTALL_DATA=$(INSTALL) -m 444
CC=/usr/bin/gcc
prefix=/usr/local
exec_prefix = $(prefix)
bindir = $(exec_prefix)/bin
libexecdir = $(exec_prefix)/libexec
datadir = $(prefix)/share
crubadandir = $(datadir)/crubadan/ga

all : cuard

install : all
	$(MAKE) installhtml
	$(INSTALL) aimsigh $(bindir)/aimsigh
	$(INSTALL) aimsigh.cgi /home/httpd/cgi-bin
	# $(INSTALL) cuard $(bindir)/cuard
	$(INSTALL) dockill $(bindir)/dockill
	$(INSTALL) seed $(bindir)/seed
	$(INSTALL) ugrep $(bindir)/ugrep
	$(INSTALL) urlkill $(bindir)/urlkill

installhtml :
	$(INSTALL_DATA) index.html ${HOME}/public_html/aimsigh
	$(INSTALL_DATA) aimsigh.css ${HOME}/public_html/aimsigh
	$(INSTALL_DATA) aimsigh.png ${HOME}/public_html/aimsigh

pillagecheck : FORCE
	(cd $(crubadandir); cat PILLAGED | sed 's/^/^url: .*/' > PILLAGED.2; find sonrai -name '*.dat' | xargs egrep -f PILLAGED.2 | egrep -v 'url: (http://www.waterfordcoco.ie/|https?://listserv.heanet.ie/)'; rm -f PILLAGED.2)

preindices : FORCE
	perl reamhinneacs NNN
	perl idf.pl
	perl reamhinneacs YNN
	perl reamhinneacs YYN
	perl c.pl
	perl reamhinneacs NNY
	perl reamhinneacs YNY
	perl reamhinneacs YYY

killdupes : FORCE
	rm -f dupescr dupelog
	perl dupe.pl
	(echo; date; cat dupelog) >> DUPELOG
	rm -f dupelog
	sort -u dupescr > dupe.tmp
	mv dupe.tmp dupescr
	echo 'look at dupescr and then bash it to actually kill the dupes'

cuard : cuard.o
	$(CC) -o $@ cuard.o

cuard.o : cuard.c
	$(CC) -c cuard.c

clean :
	rm -f *.o
FORCE :
