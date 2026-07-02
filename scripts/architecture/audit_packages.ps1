Write-Host ""
Write-Host "ATLAS PACKAGE CENSUS"
Write-Host "===================="

Get-ChildItem src\atlas -Directory |
Sort-Object Name |
ForEach-Object {

    $count = (
        Get-ChildItem $_.FullName -Recurse -Filter *.py |
        Measure-Object
    ).Count

    [PSCustomObject]@{
        Package = $_.Name
        PythonFiles = $count
    }

} | Sort-Object PythonFiles -Descending |
Format-Table -Auto