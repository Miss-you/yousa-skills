$ErrorActionPreference = "Stop"

$script:RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$script:Install = Join-Path $script:RepoRoot "install.ps1"
$script:Pass = 0
$script:Fail = 0
$script:Failures = @()
$script:Tmp = $null

function Ok([string]$Message) {
    $script:Pass += 1
    Write-Host "  PASS $Message"
}

function Bad([string]$Message) {
    $script:Fail += 1
    $script:Failures += $Message
    Write-Host "  FAIL $Message"
}

function Get-RelativePath([string]$Base, [string]$Path) {
    $basePath = [System.IO.Path]::GetFullPath($Base)
    if (-not $basePath.EndsWith([System.IO.Path]::DirectorySeparatorChar)) {
        $basePath += [System.IO.Path]::DirectorySeparatorChar
    }
    $baseUri = [System.Uri]::new($basePath)
    $pathUri = [System.Uri]::new([System.IO.Path]::GetFullPath($Path))
    [System.Uri]::UnescapeDataString($baseUri.MakeRelativeUri($pathUri).ToString()).Replace("/", [System.IO.Path]::DirectorySeparatorChar)
}

function Snapshot([string]$OutFile, [string[]]$Dirs) {
    Set-Content -LiteralPath $OutFile -Value "" -NoNewline
    foreach ($dir in $Dirs) {
        if (-not (Test-Path -LiteralPath $dir)) {
            continue
        }
        Get-ChildItem -LiteralPath $dir -Recurse -File |
            Sort-Object FullName |
            ForEach-Object {
                $relative = Get-RelativePath $dir $_.FullName
                $hash = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash
                Add-Content -LiteralPath $OutFile -Value "$hash  $relative"
            }
    }
}

function FileHash([string]$Path) {
    (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash
}

function Assert-SameTree([string]$Actual, [string]$Expected, [string]$Message) {
    if (-not (Test-Path -LiteralPath $Actual)) {
        Bad "$Message (missing $Actual)"
        return
    }

    $actualFiles = Get-ChildItem -LiteralPath $Actual -Recurse -File |
        ForEach-Object { Get-RelativePath $Actual $_.FullName } |
        Sort-Object
    $expectedFiles = Get-ChildItem -LiteralPath $Expected -Recurse -File |
        ForEach-Object { Get-RelativePath $Expected $_.FullName } |
        Sort-Object

    if (Compare-Object $actualFiles $expectedFiles) {
        Bad "$Message (file list mismatch)"
        return
    }

    foreach ($relative in $expectedFiles) {
        $actualPath = Join-Path $Actual $relative
        $expectedPath = Join-Path $Expected $relative
        if ((FileHash $actualPath) -ne (FileHash $expectedPath)) {
            Bad "$Message (content mismatch: $relative)"
            return
        }
    }

    Ok $Message
}

function New-TestEnv {
    $script:Tmp = Join-Path ([System.IO.Path]::GetTempPath()) ("yousa-install-ps1-" + [System.Guid]::NewGuid().ToString("N"))
    $script:Claude = Join-Path $script:Tmp "claude\skills"
    $script:Codex = Join-Path $script:Tmp "codex\skills"
    $script:Trae = Join-Path $script:Tmp "trae\skills"
    New-Item -ItemType Directory -Force -Path $script:Claude, $script:Codex, $script:Trae | Out-Null

    New-Item -ItemType Directory -Force -Path (Join-Path $script:Claude "foreign-a"), (Join-Path $script:Claude "foreign-b\sub") | Out-Null
    Set-Content -LiteralPath (Join-Path $script:Claude "foreign-a\SKILL.md") -Value "AAA"
    Set-Content -LiteralPath (Join-Path $script:Claude "foreign-a\extra.txt") -Value "extra-a"
    Set-Content -LiteralPath (Join-Path $script:Claude "foreign-b\SKILL.md") -Value "BBB"
    Set-Content -LiteralPath (Join-Path $script:Claude "foreign-b\sub\nested.md") -Value "nested"

    New-Item -ItemType Directory -Force -Path (Join-Path $script:Codex "foreign-c") | Out-Null
    Set-Content -LiteralPath (Join-Path $script:Codex "foreign-c\SKILL.md") -Value "CCC"

    New-Item -ItemType Directory -Force -Path (Join-Path $script:Trae "foreign-d") | Out-Null
    Set-Content -LiteralPath (Join-Path $script:Trae "foreign-d\SKILL.md") -Value "DDD"

    Set-Content -LiteralPath (Join-Path $script:Claude ".notes.txt") -Value "stray"
}

function Remove-TestEnv {
    if ($script:Tmp -and (Test-Path -LiteralPath $script:Tmp)) {
        Remove-Item -LiteralPath $script:Tmp -Recurse -Force
    }
}

function Invoke-Install([string[]]$Arguments) {
    $oldClaude = [Environment]::GetEnvironmentVariable("CLAUDE_SKILLS_DIR", "Process")
    $oldCodex = [Environment]::GetEnvironmentVariable("CODEX_SKILLS_DIR", "Process")
    $oldTrae = [Environment]::GetEnvironmentVariable("TRAE_SKILLS_DIR", "Process")
    try {
        [Environment]::SetEnvironmentVariable("CLAUDE_SKILLS_DIR", $script:Claude, "Process")
        [Environment]::SetEnvironmentVariable("CODEX_SKILLS_DIR", $script:Codex, "Process")
        [Environment]::SetEnvironmentVariable("TRAE_SKILLS_DIR", $script:Trae, "Process")
        & $script:Install @Arguments *> (Join-Path $script:Tmp "install.log")
        return $LASTEXITCODE
    } catch {
        $_ | Out-String | Set-Content -LiteralPath (Join-Path $script:Tmp "install.err")
        return 1
    } finally {
        [Environment]::SetEnvironmentVariable("CLAUDE_SKILLS_DIR", $oldClaude, "Process")
        [Environment]::SetEnvironmentVariable("CODEX_SKILLS_DIR", $oldCodex, "Process")
        [Environment]::SetEnvironmentVariable("TRAE_SKILLS_DIR", $oldTrae, "Process")
    }
}

$Skill1 = "writing-commit"
$Skill2 = "zh-proofreading"
$Skill3 = "auditing-dead-code"

Write-Host "[case 1] default install: scope is only repo skills; all three targets installed"
New-TestEnv
Snapshot (Join-Path $Tmp "before.foreign") @((Join-Path $Claude "foreign-a"), (Join-Path $Claude "foreign-b"), (Join-Path $Codex "foreign-c"), (Join-Path $Trae "foreign-d"))
$notesBefore = FileHash (Join-Path $Claude ".notes.txt")
$rc = Invoke-Install @()
if ($rc -eq 0) { Ok "exit 0" } else { Bad "exit $rc" }
Snapshot (Join-Path $Tmp "after.foreign") @((Join-Path $Claude "foreign-a"), (Join-Path $Claude "foreign-b"), (Join-Path $Codex "foreign-c"), (Join-Path $Trae "foreign-d"))
if (-not (Compare-Object (Get-Content (Join-Path $Tmp "before.foreign")) (Get-Content (Join-Path $Tmp "after.foreign")))) { Ok "AC-1: third-party skills unchanged" } else { Bad "AC-1: third-party skills changed" }
if ($notesBefore -eq (FileHash (Join-Path $Claude ".notes.txt"))) { Ok "AC-1b: stray file .notes.txt preserved" } else { Bad "AC-1b: .notes.txt mutated" }
foreach ($dir in @($Claude, $Codex, $Trae)) {
    foreach ($skill in @($Skill1, $Skill2, $Skill3)) {
        Assert-SameTree (Join-Path $dir $skill) (Join-Path $RepoRoot "skills\$skill") "installed $skill into $dir"
    }
}
Remove-TestEnv

Write-Host "[case 2] --backup: collision skill is moved to .bak, others untouched"
New-TestEnv
New-Item -ItemType Directory -Force -Path (Join-Path $Claude $Skill1) | Out-Null
Set-Content -LiteralPath (Join-Path $Claude "$Skill1\SKILL.md") -Value "OLD-VERSION"
Snapshot (Join-Path $Tmp "before.foreign") @((Join-Path $Claude "foreign-a"), (Join-Path $Claude "foreign-b"))
$rc = Invoke-Install @("--backup", "--claude-only", $Skill1)
if ($rc -eq 0) { Ok "exit 0" } else { Bad "exit $rc" }
$backupRoot = Join-Path (Split-Path -Parent $Claude) ((Split-Path -Leaf $Claude) + ".bak")
$backups = @(Get-ChildItem -LiteralPath $backupRoot -Directory -Filter "$Skill1-*" -ErrorAction SilentlyContinue)
if ($backups.Count -eq 1) { Ok "AC-3: exactly one backup at $backupRoot\$Skill1-*" } else { Bad "AC-3: expected 1 backup, found $($backups.Count)" }
if ($backups.Count -eq 1 -and (Select-String -LiteralPath (Join-Path $backups[0].FullName "SKILL.md") -Pattern "OLD-VERSION" -Quiet)) { Ok "AC-3: backup contains old version" } else { Bad "AC-3: backup missing or wrong content" }
Assert-SameTree (Join-Path $Claude $Skill1) (Join-Path $RepoRoot "skills\$Skill1") "AC-2: collision skill overwritten with repo version"
Snapshot (Join-Path $Tmp "after.foreign") @((Join-Path $Claude "foreign-a"), (Join-Path $Claude "foreign-b"))
if (-not (Compare-Object (Get-Content (Join-Path $Tmp "before.foreign")) (Get-Content (Join-Path $Tmp "after.foreign")))) { Ok "AC-1 under --backup: foreign skills unchanged" } else { Bad "AC-1 under --backup: foreign skills changed" }
$strayBak = @(Get-ChildItem -LiteralPath $Claude -Directory -Filter "*.bak*" -ErrorAction SilentlyContinue)
if ($strayBak.Count -eq 0) { Ok "AC-3: no backup pollution inside skills dir" } else { Bad "AC-3: found backup dirs inside $Claude" }
Remove-TestEnv

Write-Host "[case 2b] trailing slash in CLAUDE_SKILLS_DIR still places backup OUTSIDE"
New-TestEnv
New-Item -ItemType Directory -Force -Path (Join-Path $Claude $Skill1) | Out-Null
Set-Content -LiteralPath (Join-Path $Claude "$Skill1\SKILL.md") -Value "OLD"
$oldClaude = [Environment]::GetEnvironmentVariable("CLAUDE_SKILLS_DIR", "Process")
try {
    [Environment]::SetEnvironmentVariable("CLAUDE_SKILLS_DIR", "$Claude\", "Process")
    [Environment]::SetEnvironmentVariable("CODEX_SKILLS_DIR", $Codex, "Process")
    [Environment]::SetEnvironmentVariable("TRAE_SKILLS_DIR", $Trae, "Process")
    & $Install --backup --claude-only $Skill1 *> (Join-Path $Tmp "install.log")
    $rc = $LASTEXITCODE
} catch { $rc = 1 } finally { [Environment]::SetEnvironmentVariable("CLAUDE_SKILLS_DIR", $oldClaude, "Process") }
if ($rc -eq 0) { Ok "exit 0 with trailing slash" } else { Bad "exit $rc" }
if (Test-Path -LiteralPath (Join-Path $Claude ".bak")) { Bad "AC-3 slash: backup landed inside skills dir" } else { Ok "AC-3 slash: no .bak inside skills dir" }
if (Test-Path -LiteralPath (Join-Path (Split-Path -Parent $Claude) "skills.bak")) { Ok "AC-3 slash: backup sibling dir exists" } else { Bad "AC-3 slash: expected backup sibling dir" }
Remove-TestEnv

Write-Host "[case 3] --dry-run: zero filesystem changes"
New-TestEnv
Snapshot (Join-Path $Tmp "before.all") @($Claude, $Codex, $Trae)
$rc = Invoke-Install @("--dry-run")
if ($rc -eq 0) { Ok "exit 0" } else { Bad "exit $rc" }
Snapshot (Join-Path $Tmp "after.all") @($Claude, $Codex, $Trae)
if (-not (Compare-Object (Get-Content (Join-Path $Tmp "before.all")) (Get-Content (Join-Path $Tmp "after.all")))) { Ok "AC-4: dry-run made no changes" } else { Bad "AC-4: dry-run modified files" }
if (-not (Test-Path (Join-Path (Split-Path -Parent $Claude) "skills.bak")) -and -not (Test-Path (Join-Path (Split-Path -Parent $Codex) "skills.bak")) -and -not (Test-Path (Join-Path (Split-Path -Parent $Trae) "skills.bak"))) { Ok "AC-4: no backup roots created" } else { Bad "AC-4: dry-run created a backup root" }
Remove-TestEnv

Write-Host "[case 4] nonexistent skill name: error, no changes"
New-TestEnv
Snapshot (Join-Path $Tmp "before.all") @($Claude, $Codex, $Trae)
$rc = Invoke-Install @("does-not-exist")
if ($rc -ne 0) { Ok "AC-5: non-zero exit on bad skill name" } else { Bad "AC-5: should have failed but exited 0" }
Snapshot (Join-Path $Tmp "after.all") @($Claude, $Codex, $Trae)
if (-not (Compare-Object (Get-Content (Join-Path $Tmp "before.all")) (Get-Content (Join-Path $Tmp "after.all")))) { Ok "AC-5: no filesystem changes on error" } else { Bad "AC-5: error path mutated files" }
Remove-TestEnv

Write-Host "[case 5] --claude-only does not touch codex or trae targets"
New-TestEnv
Snapshot (Join-Path $Tmp "before.codex") @($Codex)
Snapshot (Join-Path $Tmp "before.trae") @($Trae)
$rc = Invoke-Install @("--claude-only", $Skill1)
if ($rc -eq 0) { Ok "exit 0" } else { Bad "exit $rc" }
Snapshot (Join-Path $Tmp "after.codex") @($Codex)
Snapshot (Join-Path $Tmp "after.trae") @($Trae)
if (-not (Compare-Object (Get-Content (Join-Path $Tmp "before.codex")) (Get-Content (Join-Path $Tmp "after.codex")))) { Ok "AC-7: codex target unchanged under --claude-only" } else { Bad "AC-7: codex target mutated" }
if (-not (Compare-Object (Get-Content (Join-Path $Tmp "before.trae")) (Get-Content (Join-Path $Tmp "after.trae")))) { Ok "AC-7: trae target unchanged under --claude-only" } else { Bad "AC-7: trae target mutated" }
Remove-TestEnv

Write-Host "[case 6] --codex-only does not touch claude or trae targets"
New-TestEnv
Snapshot (Join-Path $Tmp "before.claude") @($Claude)
Snapshot (Join-Path $Tmp "before.trae") @($Trae)
$rc = Invoke-Install @("--codex-only", $Skill1)
if ($rc -eq 0) { Ok "exit 0" } else { Bad "exit $rc" }
Snapshot (Join-Path $Tmp "after.claude") @($Claude)
Snapshot (Join-Path $Tmp "after.trae") @($Trae)
if (-not (Compare-Object (Get-Content (Join-Path $Tmp "before.claude")) (Get-Content (Join-Path $Tmp "after.claude")))) { Ok "AC-7: claude target unchanged under --codex-only" } else { Bad "AC-7: claude target mutated" }
if (-not (Compare-Object (Get-Content (Join-Path $Tmp "before.trae")) (Get-Content (Join-Path $Tmp "after.trae")))) { Ok "AC-7: trae target unchanged under --codex-only" } else { Bad "AC-7: trae target mutated" }
Remove-TestEnv

Write-Host "[case 7] --trae-only installs to trae and does not touch claude or codex"
New-TestEnv
Snapshot (Join-Path $Tmp "before.claude") @($Claude)
Snapshot (Join-Path $Tmp "before.codex") @($Codex)
$rc = Invoke-Install @("--trae-only", $Skill1)
if ($rc -eq 0) { Ok "exit 0" } else { Bad "exit $rc" }
Snapshot (Join-Path $Tmp "after.claude") @($Claude)
Snapshot (Join-Path $Tmp "after.codex") @($Codex)
if (-not (Compare-Object (Get-Content (Join-Path $Tmp "before.claude")) (Get-Content (Join-Path $Tmp "after.claude")))) { Ok "AC-7b: claude target unchanged under --trae-only" } else { Bad "AC-7b: claude target mutated" }
if (-not (Compare-Object (Get-Content (Join-Path $Tmp "before.codex")) (Get-Content (Join-Path $Tmp "after.codex")))) { Ok "AC-7b: codex target unchanged under --trae-only" } else { Bad "AC-7b: codex target mutated" }
Assert-SameTree (Join-Path $Trae $Skill1) (Join-Path $RepoRoot "skills\$Skill1") "AC-7b: skill installed into trae target"
Remove-TestEnv

Write-Host "[case 8] --claude-only --trae-only installs to both, skipping codex"
New-TestEnv
Snapshot (Join-Path $Tmp "before.codex") @($Codex)
$rc = Invoke-Install @("--claude-only", "--trae-only", $Skill1)
if ($rc -eq 0) { Ok "exit 0" } else { Bad "exit $rc" }
Snapshot (Join-Path $Tmp "after.codex") @($Codex)
if (-not (Compare-Object (Get-Content (Join-Path $Tmp "before.codex")) (Get-Content (Join-Path $Tmp "after.codex")))) { Ok "AC-7c: codex target unchanged under --claude-only --trae-only" } else { Bad "AC-7c: codex target mutated" }
Assert-SameTree (Join-Path $Claude $Skill1) (Join-Path $RepoRoot "skills\$Skill1") "AC-7c: skill installed into claude target"
Assert-SameTree (Join-Path $Trae $Skill1) (Join-Path $RepoRoot "skills\$Skill1") "AC-7c: skill installed into trae target"
Remove-TestEnv

Write-Host "[case 9] idempotent: two runs in a row converge"
New-TestEnv
[void](Invoke-Install @())
Snapshot (Join-Path $Tmp "run1") @($Claude, $Codex, $Trae)
[void](Invoke-Install @())
Snapshot (Join-Path $Tmp "run2") @($Claude, $Codex, $Trae)
if (-not (Compare-Object (Get-Content (Join-Path $Tmp "run1")) (Get-Content (Join-Path $Tmp "run2")))) { Ok "AC-8: idempotent" } else { Bad "AC-8: second run changed state" }
Remove-TestEnv

Write-Host "[case 10] '--' separator works"
New-TestEnv
$rc = Invoke-Install @("--claude-only", "--", $Skill1)
if ($rc -eq 0) { Ok "AC-9: -- separator: exit 0" } else { Bad "AC-9: -- separator exit $rc" }
if (Test-Path -LiteralPath (Join-Path $Claude $Skill1)) { Ok "AC-9: -- consumed and skill installed" } else { Bad "AC-9: skill not installed after --" }
$rc = Invoke-Install @("--claude-only", "--dry-run", "--")
if ($rc -eq 0) { Ok "AC-9b: bare -- exit 0" } else { Bad "AC-9b: bare -- exit $rc" }
Remove-TestEnv

Write-Host "[case 11] metacharacter skill name is rejected without command execution"
New-TestEnv
$canary = Join-Path $Tmp "canary"
$rc = Invoke-Install @("`$(New-Item -Path '$canary')")
if ($rc -ne 0) { Ok "case11: tricky skill name rejected" } else { Bad "case11: tricky skill name accepted" }
if (-not (Test-Path -LiteralPath $canary)) { Ok "case11: no command execution" } else { Bad "case11: canary file created" }
Remove-TestEnv

Write-Host ""
Write-Host "Summary: $Pass passed, $Fail failed"
if ($Fail -gt 0) {
    Write-Host ""
    Write-Host "Failures:"
    foreach ($message in $Failures) {
        Write-Host "  - $message"
    }
    exit 1
}
exit 0
