$ErrorActionPreference = 'Stop'

function Write-Section([string] $Title) {
    Write-Host "`n=== $Title ===" -ForegroundColor Cyan
}

function Invoke-Fresh([string[]] $Arguments) {
    & fresh @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "fresh $($Arguments -join ' ') failed with exit code $LASTEXITCODE"
    }
}

function Show-MedianRuntime([string] $Label, [scriptblock] $Action) {
    & $Action *> $null # Warm up the process path.
    $samples = @()
    for ($sample = 0; $sample -lt 5; $sample++) {
        $samples += (Measure-Command { & $Action *> $null }).TotalMilliseconds
    }
    $ordered = @($samples | Sort-Object)
    Write-Host ("{0}: {1:N1} ms median (five runs; includes process startup)" -f $Label, $ordered[2])
}

if (-not (Get-Command fresh -ErrorAction SilentlyContinue)) {
    throw "The 'fresh' command is not on PATH. Open this script from the Fresh project environment."
}

$repo = $PSScriptRoot
$pythonCommand = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCommand) {
    throw "Python is needed for the side-by-side performance scenarios."
}
$pythonExe = $pythonCommand.Source
Push-Location $repo
$nativeProject = Join-Path $repo (".fresh-review-" + [guid]::NewGuid().ToString('N'))
$typeErrorFile = Join-Path $nativeProject 'intentional_type_error.fresh'

try {
    Write-Section '1. Functions, recursion, and inferred local types'
    Invoke-Fresh @('run', 'examples/01_fibonacci.fresh')

    Write-Section '2. Compile-time type checking and diagnostics'
    New-Item -ItemType Directory -Path $nativeProject -Force | Out-Null
    [System.IO.File]::WriteAllText($typeErrorFile, 'let x: int = "hello";', [System.Text.UTF8Encoding]::new($false))
    # Windows PowerShell 5.1 turns redirected native stderr into an ErrorRecord.
    # This command is expected to fail; inspect its exit code and message below.
    $previousErrorAction = $ErrorActionPreference
    try {
        $ErrorActionPreference = 'Continue'
        $diagnosticOutput = & fresh check $typeErrorFile 2>&1
        $diagnosticExit = $LASTEXITCODE
    }
    finally {
        $ErrorActionPreference = $previousErrorAction
    }
    $diagnosticText = ($diagnosticOutput | ForEach-Object { $_.ToString() }) -join "`n"
    Write-Host $diagnosticText
    if ($diagnosticExit -eq 0 -or
        $diagnosticText -notmatch 'FreshTypeError' -or
        $diagnosticText -notmatch "Cannot initialize variable 'x' of type 'int' with value of type 'string'") {
        throw 'The intentional type-error example did not produce the expected compile-time diagnostic.'
    }
    Write-Host "Expected compile-time rejection observed (exit $diagnosticExit)."

    Write-Section '3. Closures, captured state, structs, and arrays'
    Invoke-Fresh @('run', 'examples/04_closure_counter.fresh')
    Invoke-Fresh @('run', 'examples/06_inventory.fresh')

    Write-Section '4. GC stress mode: live closure state survives collection'
    $previousGcStress = $env:FRESH_GC_STRESS
    try {
        $env:FRESH_GC_STRESS = '1'
        Invoke-Fresh @('run', 'examples/04_closure_counter.fresh')
    }
    finally {
        if ($null -eq $previousGcStress) {
            Remove-Item Env:FRESH_GC_STRESS -ErrorAction SilentlyContinue
        }
        else {
            $env:FRESH_GC_STRESS = $previousGcStress
        }
    }

    Write-Section '5. Classes, inheritance, and method overriding'
    Invoke-Fresh @('run', 'examples/oop_demo.fresh')
    Invoke-Fresh @('check', 'examples/oop_demo.fresh')
    Invoke-Fresh @('run', 'examples/oop_demo.fresh', '--dump-ast')
    Invoke-Fresh @('run', 'examples/oop_demo.fresh', '--disassemble')

    Write-Section '6. Algorithms and complete language showcases'
    Invoke-Fresh @('run', 'examples/02_matrix_multiply.fresh')
    Invoke-Fresh @('run', 'examples/03_quicksort.fresh')
    Invoke-Fresh @('run', 'examples/05_calculator.fresh')
    Invoke-Fresh @('run', 'examples/08_aggressive_suite.fresh')
    Invoke-Fresh @('run', 'demo/quick_demo.fresh')
    Push-Location $nativeProject
    try {
        # These programs use relative file I/O paths. Keep their output out of the repository.
        Invoke-Fresh @('run', (Join-Path $repo 'examples/07_stress_suite.fresh'))
        Invoke-Fresh @('run', (Join-Path $repo 'all_features.fresh'))
        Invoke-Fresh @('run', (Join-Path $repo 'demo/master_showcase.fresh'))
    }
    finally {
        Pop-Location
    }

    Write-Section '7. Compiler inspection'
    Invoke-Fresh @('run', 'examples/01_fibonacci.fresh', '--dump-tokens')
    Invoke-Fresh @('run', 'examples/01_fibonacci.fresh', '--dump-ast')
    Invoke-Fresh @('run', 'examples/01_fibonacci.fresh', '--disassemble')
    Invoke-Fresh @('run', 'examples/01_fibonacci.fresh', '--emit-c')

    Write-Section '8. CLI tooling: check, format, init, tests, and native build'
    Invoke-Fresh @('check', 'demo/quick_demo.fresh')
    $formatFile = Join-Path $nativeProject 'format_demo.fresh'
    Copy-Item -LiteralPath (Join-Path $repo 'demo/quick_demo.fresh') -Destination $formatFile
    Invoke-Fresh @('fmt', $formatFile)
    Invoke-Fresh @('fmt', $formatFile, '--check')

    $previousTemp = $env:TEMP
    $previousTmp = $env:TMP
    try {
        $env:TEMP = $nativeProject
        $env:TMP = $nativeProject
        Invoke-Fresh @('test', 'tests/cli')
    }
    finally {
        $env:TEMP = $previousTemp
        $env:TMP = $previousTmp
    }

    Invoke-Fresh @('init', 'review_demo', '--dir', $nativeProject)
    $buildProject = Join-Path $nativeProject 'review_demo'
    $sourceDir = Join-Path $buildProject 'src'
    Invoke-Fresh @('build', $buildProject)
    $nativeExe = Join-Path $buildProject 'build/review_demo.exe'
    if (-not (Test-Path $nativeExe)) {
        throw "Native executable was not created at $nativeExe"
    }
    & $nativeExe
    if ($LASTEXITCODE -ne 0) {
        throw "Native executable failed with exit code $LASTEXITCODE"
    }

    Write-Section '9. Two native Fresh vs Python speed scenarios'
    Write-Host 'These compare Fresh-generated native C with Python. They do not measure Fresh VM GC.'
    $pythonSum = Join-Path $nativeProject 'sum.py'
    [System.IO.File]::WriteAllLines((Join-Path $sourceDir 'main.fresh'), @(
        'fn sum_to(n: int) -> int {',
        '    let total = 0;',
        '    for (let i = 0; i <= n; i = i + 1) { total = total + i; }',
        '    return total;',
        '}',
        'println(sum_to(20000000));'
    ), [System.Text.UTF8Encoding]::new($false))
    [System.IO.File]::WriteAllLines($pythonSum, @(
        'total = 0',
        'for i in range(20_000_001):',
        '    total += i',
        'print(total)'
    ), [System.Text.UTF8Encoding]::new($false))
    Invoke-Fresh @('build', $buildProject)
    $nativeSum = (& $nativeExe | Out-String).Trim()
    if ($LASTEXITCODE -ne 0) { throw 'Native integer-loop scenario failed.' }
    $pythonSumOutput = (& $pythonExe $pythonSum | Out-String).Trim()
    if ($LASTEXITCODE -ne 0 -or $nativeSum -ne $pythonSumOutput -or $nativeSum -ne '200000010000000') {
        throw 'Integer-loop scenario outputs did not match.'
    }
    Write-Host "Both outputs: $nativeSum"
    Show-MedianRuntime 'Fresh native integer loop' { & $nativeExe }
    Show-MedianRuntime 'Python integer loop' { & $pythonExe $pythonSum }

    $pythonFib = Join-Path $nativeProject 'fib.py'
    [System.IO.File]::WriteAllLines((Join-Path $sourceDir 'main.fresh'), @(
        'fn fib(n: int) -> int {',
        '    if (n <= 1) { return n; }',
        '    return fib(n - 1) + fib(n - 2);',
        '}',
        'println(fib(32));'
    ), [System.Text.UTF8Encoding]::new($false))
    [System.IO.File]::WriteAllLines($pythonFib, @(
        'def fib(n):',
        '    if n <= 1: return n',
        '    return fib(n - 1) + fib(n - 2)',
        'print(fib(32))'
    ), [System.Text.UTF8Encoding]::new($false))
    Invoke-Fresh @('build', $buildProject)
    $nativeFib = (& $nativeExe | Out-String).Trim()
    if ($LASTEXITCODE -ne 0) { throw 'Native recursion scenario failed.' }
    $pythonFibOutput = (& $pythonExe $pythonFib | Out-String).Trim()
    if ($LASTEXITCODE -ne 0 -or $nativeFib -ne $pythonFibOutput -or $nativeFib -ne '2178309') {
        throw 'Recursive Fibonacci scenario outputs did not match.'
    }
    Write-Host "Both outputs: $nativeFib"
    Show-MedianRuntime 'Fresh native recursive Fibonacci' { & $nativeExe }
    Show-MedianRuntime 'Python recursive Fibonacci' { & $pythonExe $pythonFib }

    Write-Section 'Demo complete'
}
finally {
    Pop-Location
    if (Test-Path -LiteralPath $nativeProject) {
        $resolvedRepo = (Resolve-Path -LiteralPath $repo).Path.TrimEnd('\')
        $resolvedProject = (Resolve-Path -LiteralPath $nativeProject).Path
        if (-not $resolvedProject.StartsWith($resolvedRepo + '\', [System.StringComparison]::OrdinalIgnoreCase) -or
            -not ([System.IO.Path]::GetFileName($resolvedProject)).StartsWith('.fresh-review-')) {
            throw "Refusing to remove unexpected demo directory: $resolvedProject"
        }
        Remove-Item -LiteralPath $nativeProject -Recurse -Force
    }
}
