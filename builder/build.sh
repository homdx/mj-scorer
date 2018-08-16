rm ZAPSMahjongScorer-*release*.apk

buildozer android release

/home/kivy/.buildozer/android/platform/android-sdk-20/build-tools/23.0.1/zipalign -v 4 ZAPSMahjongScorer-0.1.3-release-unsigned.apk ZAPSMahjongScorer-0.1.3-release.apk

jarsigner -verbose -sigalg SHA1withRSA -digestalg SHA1 -keystore ~/keystores/es-bacchant-mj.keystore ZAPSMahjongScorer-0.1.3-release.apk mj

