#Region ;**** Directives created by AutoIt3Wrapper_GUI ****
#AutoIt3Wrapper_Res_Fileversion=1.0.3.0
#EndRegion ;**** Directives created by AutoIt3Wrapper_GUI ****
#include <AutoItConstants.au3>
HotKeySet("{PAUSE}", "pause")
HotKeySet("{NUMPADADD}", "volChange")
HotKeySet("{NUMPADSUB}", "volChange")
HotKeySet("{NUMPADDIV}", "stop")

Global $paused = 0
Global $volume = 0.2

Func volChange()
	Switch @HotKeyPressed
		Case "{NUMPADSUB}"
			If $volume > 0 Then
				$volume -= 0.05
			EndIf
		Case "{NUMPADADD}"
			If $volume < 1 Then
				$volume += 0.05
			EndIf
	EndSwitch
	Run("NirCmd.exe setappvolume chrome.exe " & $volume, @DesktopDir, @SW_HIDE)
EndFunc   ;==>volChange

Func pause()
	If $paused = 0 Then
		$paused = 1
	ElseIf $paused = 1 Then
		$paused = 0
	EndIf
	While $paused = 1
		Sleep(1000)
	WEnd
EndFunc   ;==>pause

Func stop()
	Exit
EndFunc   ;==>stop

Run("NirCmd.exe setappvolume chrome.exe 0.2", @DesktopDir, @SW_HIDE) ; Set the volume to 20%
While True
	Sleep(100)
WEnd

