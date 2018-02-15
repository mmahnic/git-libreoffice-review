#!/usr/bin/env bash

package=CodeReview
ident=com.github.mmahnic.codereview
version=0.1.20

buildroot=../build

loextroot=$buildroot/loext
if [ ! -d $loextroot ]; then
   mkdir $loextroot
fi

# Template variables
export oxt_version=$version
export oxt_ident=$ident

# Update the sources in buildroot and expand the variables in updated files.
cp -ru ./CodeReview  $loextroot/
for fn in $(find $loextroot -type f | xargs grep -l -e '\${oxt_[_a-z]\+}' | cut -b${#loextroot}- | cut -b3-)
do
   echo "envsubst $fn"
   cat $fn | envsubst > $loextroot/$fn
done

# Pack the generated files
pushd $loextroot/CodeReview
zipfile=../$package-$version.oxt
if [ -f $zipfile ]; then
   rm $zipfile
fi
zip -r $zipfile  *
popd
