#define MyAppName "ImageType"
#define MyAppVersion "3.0.0"
#define MyAppPublisher "Ahmed Samy Elkhouly"
#define MyAppURL "https://github.com/ahmedthebest31/ImageType"
#define MyAppExeName "ImageType.exe"

[Setup]
AppId={{47FBF3C9-8EFB-4AC3-A6E4-665B9F530932}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}

DefaultDirName={localappdata}\{#MyAppName}
UninstallDisplayIcon={app}\{#MyAppExeName}

ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

DisableProgramGroupPage=yes
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=commandline

VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription=An application for adding text to images with screen reader compatibility.
VersionInfoVersion={#MyAppVersion}
VersionInfoProductVersion={#MyAppVersion}
VersionInfoProductName={#MyAppName}
VersionInfoCopyright=Copyright (c) 2026 Ahmed Samy Elkhouly

OutputDir=output
OutputBaseFilename=ImageType_Setup
SetupIconFile=assets\icon_64.ico
SolidCompression=yes
WizardStyle=modern dynamic

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "arabic"; MessagesFile: "compiler:Languages\Arabic.isl"
Name: "dutch"; MessagesFile: "compiler:Languages\Dutch.isl"
Name: "finnish"; MessagesFile: "compiler:Languages\Finnish.isl"
Name: "german"; MessagesFile: "compiler:Languages\German.isl"
Name: "italian"; MessagesFile: "compiler:Languages\Italian.isl"
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "pyproject.toml"; DestDir: "{app}"; DestName: "installed.tag"; Flags: ignoreversion

Source: "languages\*"; DestDir: "{userdocs}\Ahmed Samy\ImageType\languages"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "themes\*"; DestDir: "{userdocs}\Ahmed Samy\ImageType\themes"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "fonts\*"; DestDir: "{userdocs}\Ahmed Samy\ImageType\fonts"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "templates\*"; DestDir: "{userdocs}\Ahmed Samy\ImageType\templates"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent