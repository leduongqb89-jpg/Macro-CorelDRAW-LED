; Bo cai AutoLED Pro (Inno Setup 6)
#define MyAppName "AutoLED Pro"
#define MyAppVersion "3.0.0"
#define MyAppExe "AutoLEDPro.exe"

[Setup]
AppId={{8E6F2C3A-5B1D-4C7E-9A2F-1D3B4C5E6F70}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher=AutoLED Pro
DefaultDirName={autopf}\AutoLED Pro
DefaultGroupName=AutoLED Pro
DisableProgramGroupPage=yes
OutputDir=..\dist_installer
OutputBaseFilename=AutoLEDPro-Setup-{#MyAppVersion}
SetupIconFile=..\app\assets\autoled.ico
UninstallDisplayIcon={app}\{#MyAppExe}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Tạo biểu tượng AutoLED Pro ngoài Desktop"; GroupDescription: "Biểu tượng:"

[Files]
Source: "..\dist\AutoLEDPro\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\AutoLEDPro.bas"; DestDir: "{app}\macro_VBA"; Flags: ignoreversion
Source: "..\clsAutoLEDEvt.cls"; DestDir: "{app}\macro_VBA"; Flags: ignoreversion
Source: "..\frmAutoLED_code.txt"; DestDir: "{app}\macro_VBA"; Flags: ignoreversion
Source: "..\installer\HUONG_DAN.txt"; DestDir: "{app}"; Flags: ignoreversion isreadme

[Icons]
Name: "{group}\AutoLED Pro"; Filename: "{app}\{#MyAppExe}"; IconFilename: "{app}\{#MyAppExe}"
Name: "{group}\Hướng dẫn AutoLED Pro"; Filename: "{app}\HUONG_DAN.txt"
Name: "{group}\Gỡ cài đặt AutoLED Pro"; Filename: "{uninstallexe}"
Name: "{autodesktop}\AutoLED Pro"; Filename: "{app}\{#MyAppExe}"; IconFilename: "{app}\{#MyAppExe}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExe}"; Description: "Mở AutoLED Pro ngay"; Flags: nowait postinstall skipifsilent
