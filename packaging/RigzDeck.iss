; RigzDeck Installer (Inno Setup).
; Vorher:  .\packaging\build.ps1   (erzeugt dist\RigzDeck\)
; Bauen:   ISCC.exe packaging\RigzDeck.iss   (Inno Setup Compiler)
#define AppName "RigzDeck"
#define AppVersion "0.7.3"
#define AppPublisher "RitschyRigz"
#define AppExe "RigzDeck.exe"

[Setup]
AppId={{8F3A1C7E-2B5D-4E9A-A1C3-9D2E4F6B8A10}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
OutputDir=..\dist\installer
OutputBaseFilename={#AppName}-{#AppVersion}-setup
SetupIconFile=..\web\public\monogram.ico
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "de"; MessagesFile: "compiler:Languages\German.isl"
Name: "en"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

; Autostart wird im Tray verwaltet (RigzDeck-Tray -> "Mit Windows starten": Aus / nur Tray / mit Fenster) —
; NICHT per Installer (zwei konkurrierende Autostarts = zwei Instanzen). Alte Autostart-Verknuepfung aufraeumen:
[InstallDelete]
Type: files; Name: "{userstartup}\{#AppName}.lnk"

[Files]
Source: "..\dist\RigzDeck\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExe}"
Name: "{group}\{cm:UninstallProgram,{#AppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExe}"; Description: "{cm:LaunchProgram,{#AppName}}"; Flags: nowait postinstall skipifsilent
