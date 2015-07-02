#!/bin/bash
find ../.. -name \*.py | xargs xgettext --language=Python -cNOTE -o otrs_us.pot
msguniq  otrs_us.pot -u -o otrs_us.pot
for i in *.po
do
    msgmerge -U "$i" otrs_us.pot
    fnam="../locale/${i%.po}/LC_MESSAGES/otrs_us.mo"
    if [ ! -d "../locale/${i%.po}/LC_MESSAGES" ]
    then
	mkdir -p "../locale/${i%.po}/LC_MESSAGES"
    fi
    if [ "$i" -nt "$fnam" ] 
    then
	echo $fnam
	rm -f "$fnam"
	msgfmt "$i" -o "$fnam"
    fi
done


