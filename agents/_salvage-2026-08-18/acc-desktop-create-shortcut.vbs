Set oShell = CreateObject("WScript.Shell")
Set oLink = oShell.CreateShortcut(oShell.SpecialFolders("Desktop") & "\Agent Control Center.lnk")
oLink.TargetPath = oShell.ExpandEnvironmentStrings("%LOCALAPPDATA%") & "\hermes\hermes-agent\node_modules\.bin\electron.cmd"
oLink.Arguments = oShell.ExpandEnvironmentStrings("%USERPROFILE%") & "\acc-desktop"
oLink.WorkingDirectory = oShell.ExpandEnvironmentStrings("%USERPROFILE%") & "\acc-desktop"
oLink.Description = "Agent Control Center — управление ИИ-агентами"
oLink.Save
