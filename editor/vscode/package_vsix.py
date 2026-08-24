from __future__ import annotations

import json
import zipfile
from html import escape
from pathlib import Path


ROOT = Path(__file__).resolve().parent
FIXED_TIME = (2024, 1, 1, 0, 0, 0)


def main() -> int:
    package = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
    output = ROOT / f"{package['name']}-{package['version']}.vsix"
    files = [
        (ROOT / "extension.ts", "extension/extension.ts"),
        (ROOT / "LICENSE.txt", "extension/LICENSE.txt"),
        (ROOT / "README.md", "extension/readme.md"),
        (ROOT / "package.json", "extension/package.json"),
    ]
    files.extend(
        (path, f"extension/{path.relative_to(ROOT).as_posix()}")
        for path in sorted((ROOT / "out").glob("*.js*"))
    )
    manifest = _manifest(package).encode("utf-8")
    content_types = _content_types().encode("utf-8")
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        _write(archive, "[Content_Types].xml", content_types)
        _write(archive, "extension.vsixmanifest", manifest)
        for source, target in sorted(files, key=lambda item: item[1]):
            _write(archive, target, source.read_bytes())
    print(output)
    return 0


def _write(archive: zipfile.ZipFile, name: str, content: bytes) -> None:
    info = zipfile.ZipInfo(name, FIXED_TIME)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o644 << 16
    archive.writestr(info, content)


def _manifest(package: dict[str, object]) -> str:
    categories = ",".join(str(value) for value in package.get("categories", []))
    return f'''<?xml version="1.0" encoding="utf-8"?>
<PackageManifest Version="2.0.0" xmlns="http://schemas.microsoft.com/developer/vsx-schema/2011">
  <Metadata>
    <Identity Language="en-US" Id="{escape(str(package['name']))}" Version="{escape(str(package['version']))}" Publisher="{escape(str(package['publisher']))}" />
    <DisplayName>{escape(str(package['displayName']))}</DisplayName>
    <Description xml:space="preserve">{escape(str(package['description']))}</Description>
    <Categories>{escape(categories)}</Categories>
    <GalleryFlags>Public</GalleryFlags>
    <Properties>
      <Property Id="Microsoft.VisualStudio.Code.Engine" Value="{escape(str(package['engines']['vscode']))}" />
      <Property Id="Microsoft.VisualStudio.Code.ExtensionKind" Value="workspace" />
      <Property Id="Microsoft.VisualStudio.Code.ExecutesCode" Value="true" />
      <Property Id="Microsoft.VisualStudio.Services.GitHubFlavoredMarkdown" Value="true" />
      <Property Id="Microsoft.VisualStudio.Services.Content.Pricing" Value="Free" />
    </Properties>
    <License>extension/LICENSE.txt</License>
  </Metadata>
  <Installation><InstallationTarget Id="Microsoft.VisualStudio.Code" /></Installation>
  <Dependencies />
  <Assets>
    <Asset Type="Microsoft.VisualStudio.Code.Manifest" Path="extension/package.json" Addressable="true" />
    <Asset Type="Microsoft.VisualStudio.Services.Content.Details" Path="extension/readme.md" Addressable="true" />
    <Asset Type="Microsoft.VisualStudio.Services.Content.License" Path="extension/LICENSE.txt" Addressable="true" />
  </Assets>
</PackageManifest>
'''


def _content_types() -> str:
    return '''<?xml version="1.0" encoding="utf-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension=".js" ContentType="application/javascript" />
  <Default Extension=".json" ContentType="application/json" />
  <Default Extension=".map" ContentType="application/json" />
  <Default Extension=".md" ContentType="text/markdown" />
  <Default Extension=".ts" ContentType="video/mp2t" />
  <Default Extension=".txt" ContentType="text/plain" />
  <Default Extension=".vsixmanifest" ContentType="text/xml" />
</Types>
'''


if __name__ == "__main__":
    raise SystemExit(main())
