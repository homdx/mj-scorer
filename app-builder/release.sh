#!/bin/bash

rm ZAPSMahjongScorer-*release*.apk ZAPSMahjongScorer-*-.apk

buildozer android release

for f in $(find . -name 'ZAPSMahjongScorer*-unsigned.apk')
do
    t=${f%*-release-unsigned.apk}
done

/home/kivy/.buildozer/android/platform/android-sdk-20/build-tools/23.0.1/zipalign -v 4 $f $t-.apk

jarsigner -storepass android -verbose -sigalg SHA1withRSA -digestalg SHA1 -keystore ~/keystores/es-bacchant-mj.keystore $t-.apk mj

