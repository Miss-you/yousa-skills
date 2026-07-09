$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$SrcDir = Join-Path $ScriptDir "skills"

function Write-Usage {
    $scriptName = Split-Path -Leaf $MyInvocation.ScriptName
    @"
Usage: .\$scriptName [options] [skill-name ...]

Install skills from $SrcDir into personal skill directories.
With no skill names, installs every skill under skills/.

Targets (default: all three):
  --claude-only        Install to `$env:CLAUDE_SKILLS_DIR (default: ~/.claude/skills)
  --codex-only         Install to `$env:CODEX_SKILLS_DIR  (default: ~/.codex/skills)
  --trae-only          Install to `$env:TRAE_SKILLS_DIR   (default: ~/.trae-cn/skills)

  The --*-only flags are additive: pass several to install to a chosen subset.
  For example: --claude-only --trae-only installs to Claude and Trae, skipping
  Codex.

Behavior:
  --backup             Move existing <skill>/ to <target>.bak/<skill>-<timestamp>-<pid>/
                       before overwriting. Default is plain overwrite.
                       Backups live OUTSIDE the skills dir so the host (Claude/
                       Codex/Trae) does not load them as duplicate skills.
  --dry-run            Print planned actions without changing anything.
  --list               List skills available in this repo and exit.
  -h, --help           Show this help.

Env overrides:
  CLAUDE_SKILLS_DIR    Override Claude target directory.
  CODEX_SKILLS_DIR     Override Codex target directory.
  TRAE_SKILLS_DIR      Override Trae target directory.
"@
}

function Die([string]$Message) {
    Write-Error "error: $Message"
    exit 1
}

function Trim-TrailingSeparators([string]$Path) {
    if ([string]::IsNullOrWhiteSpace($Path)) {
        return $Path
    }

    $fullPath = [System.IO.Path]::GetFullPath($Path)
    $root = [System.IO.Path]::GetPathRoot($fullPath)
    while ($fullPath.Length -gt $root.Length -and ($fullPath.EndsWith("\") -or $fullPath.EndsWith("/"))) {
        $fullPath = $fullPath.Substring(0, $fullPath.Length - 1)
    }
    return $fullPath
}

function Env-OrDefault([string]$Name, [string]$Default) {
    $value = [Environment]::GetEnvironmentVariable($Name, "Process")
    if ([string]::IsNullOrWhiteSpace($value)) {
        return $Default
    }
    return $value
}

function Run-Action([scriptblock]$Action, [string]$DryRunText) {
    if ($script:DryRun) {
        Write-Host "  + $DryRunText"
    } else {
        & $Action
    }
}

function Copy-Skill([string]$Source, [string]$Destination) {
    Run-Action {
        if (Test-Path -LiteralPath $Destination) {
            Remove-Item -LiteralPath $Destination -Recurse -Force
        }
        Copy-Item -LiteralPath $Source -Destination $Destination -Recurse -Force
    } "copy `"$Source`" `"$Destination`""
}

$ClaudeDir = Trim-TrailingSeparators (Env-OrDefault "CLAUDE_SKILLS_DIR" (Join-Path $HOME ".claude\skills"))
$CodexDir = Trim-TrailingSeparators (Env-OrDefault "CODEX_SKILLS_DIR" (Join-Path $HOME ".codex\skills"))
$TraeDir = Trim-TrailingSeparators (Env-OrDefault "TRAE_SKILLS_DIR" (Join-Path $HOME ".trae-cn\skills"))

$InstallClaude = $true
$InstallCodex = $true
$InstallTrae = $true
$script:DryRun = $false
$DoBackup = $false
$DoList = $false
$OnlyMode = $false
$Selected = New-Object System.Collections.Generic.List[string]

$remaining = @($args)
for ($i = 0; $i -lt $remaining.Count; $i++) {
    $arg = $remaining[$i]
    switch ($arg) {
        "--claude-only" {
            if (-not $OnlyMode) {
                $InstallClaude = $false
                $InstallCodex = $false
                $InstallTrae = $false
                $OnlyMode = $true
            }
            $InstallClaude = $true
            continue
        }
        "--codex-only" {
            if (-not $OnlyMode) {
                $InstallClaude = $false
                $InstallCodex = $false
                $InstallTrae = $false
                $OnlyMode = $true
            }
            $InstallCodex = $true
            continue
        }
        "--trae-only" {
            if (-not $OnlyMode) {
                $InstallClaude = $false
                $InstallCodex = $false
                $InstallTrae = $false
                $OnlyMode = $true
            }
            $InstallTrae = $true
            continue
        }
        "--backup" {
            $DoBackup = $true
            continue
        }
        "--dry-run" {
            $script:DryRun = $true
            continue
        }
        "--list" {
            $DoList = $true
            continue
        }
        { $_ -eq "-h" -or $_ -eq "--help" } {
            Write-Usage
            exit 0
        }
        "--" {
            for ($j = $i + 1; $j -lt $remaining.Count; $j++) {
                $Selected.Add($remaining[$j])
            }
            break
        }
        default {
            if ($arg.StartsWith("-")) {
                Die "unknown option: $arg (try --help)"
            }
            $Selected.Add($arg)
        }
    }
}

if (-not (Test-Path -LiteralPath $SrcDir -PathType Container)) {
    Die "skills source not found: $SrcDir"
}

$Available = Get-ChildItem -LiteralPath $SrcDir -Directory |
    Where-Object { Test-Path -LiteralPath (Join-Path $_.FullName "SKILL.md") -PathType Leaf } |
    Select-Object -ExpandProperty Name |
    Sort-Object

if ($DoList) {
    $Available | ForEach-Object { Write-Host $_ }
    exit 0
}

if ($Selected.Count -eq 0) {
    $ToInstall = @($Available)
} else {
    $ToInstall = @()
    foreach ($name in $Selected) {
        if ($Available -notcontains $name) {
            Die "skill not found in repo: $name"
        }
        $ToInstall += $name
    }
}

if ($ToInstall.Count -eq 0) {
    Die "no skills to install"
}

$Targets = @()
if ($InstallClaude) { $Targets += $ClaudeDir }
if ($InstallCodex) { $Targets += $CodexDir }
if ($InstallTrae) { $Targets += $TraeDir }
if ($Targets.Count -eq 0) {
    Die "no install targets selected"
}

$Timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$Installed = 0
$Upgraded = 0
$BackedUp = 0

Write-Host "source : $SrcDir"
foreach ($target in $Targets) {
    Write-Host "target : $target"
}
$skillMode = if ($Selected.Count -eq 0) { "all" } else { "selected" }
Write-Host "skills : $($ToInstall.Count) ($skillMode)"
if ($script:DryRun) {
    Write-Host "mode   : dry-run (no changes)"
}
Write-Host ""

foreach ($target in $Targets) {
    if (-not (Test-Path -LiteralPath $target -PathType Container)) {
        Write-Host "creating target dir: $target"
        Run-Action { New-Item -ItemType Directory -Force -Path $target | Out-Null } "mkdir `"$target`""
    }

    foreach ($name in $ToInstall) {
        $src = Join-Path $SrcDir $name
        $dst = Join-Path $target $name
        $action = "install"

        if (Test-Path -LiteralPath $dst) {
            $action = "upgrade"
            if ($DoBackup) {
                $backupRoot = "$target.bak"
                $backup = Join-Path $backupRoot "$name-$Timestamp-$PID"
                if (Test-Path -LiteralPath $backup) {
                    Die "backup path already exists: $backup (refusing to clobber)"
                }
                Write-Host "backup : $dst -> $backup"
                Run-Action { New-Item -ItemType Directory -Force -Path $backupRoot | Out-Null } "mkdir `"$backupRoot`""
                Run-Action { Move-Item -LiteralPath $dst -Destination $backup } "move `"$dst`" `"$backup`""
                $BackedUp += 1
            }
        }

        Write-Host "${action}: $name -> $target"
        Copy-Skill $src $dst
        if ($action -eq "upgrade") {
            $Upgraded += 1
        } else {
            $Installed += 1
        }
    }
}

Write-Host ""
Write-Host "done. installed=$Installed upgraded=$Upgraded backed_up=$BackedUp"
if ($script:DryRun) {
    Write-Host "(dry-run: nothing was written)"
}
exit 0
