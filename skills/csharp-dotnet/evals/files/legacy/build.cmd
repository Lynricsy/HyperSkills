@echo off
rem CI entry point (Windows agent, VS 2022 Build Tools). Do not replace with dotnet test:
rem Billing.Tests is a .NET Framework 4.8 non-SDK project restored from packages.config.
nuget restore Billing.sln || exit /b 1
msbuild Billing.sln /p:Configuration=Release /m || exit /b 1
"%VSINSTALLDIR%Common7\IDE\Extensions\TestPlatform\vstest.console.exe" Billing.Tests\bin\Release\Billing.Tests.dll /logger:trx || exit /b 1
