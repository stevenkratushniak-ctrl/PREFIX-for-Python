"""Verify the finished VSIX against compiled source; this is not a host test."""
from __future__ import annotations
import argparse,hashlib,json,zipfile
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
README_TRANSFORMS={
    "assets/actual-enter-demo.gif":"https://github.com/stevenkratushniak-ctrl/PREFIX-for-Python/raw/refs/heads/codex/prefix-distribution-001/editor/vscode/assets/actual-enter-demo.gif",
    "PRIVACY.md":"https://github.com/stevenkratushniak-ctrl/PREFIX-for-Python/blob/codex/prefix-distribution-001/editor/vscode/PRIVACY.md",
    "SUPPORT.md":"https://github.com/stevenkratushniak-ctrl/PREFIX-for-Python/blob/codex/prefix-distribution-001/editor/vscode/SUPPORT.md"
}
def digest(data): return hashlib.sha256(data).hexdigest()
def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--source",type=Path,default=ROOT)
    parser.add_argument("--vsix",type=Path,required=True)
    parser.add_argument("--expected-sha256",required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    editor=args.source.resolve()/"editor"/"vscode"
    report={"schema":"prefix-finished-vsix-parity.v1","vsix":str(args.vsix.resolve()),"checks":[],"actual_host_test":False}
    def check(name,passed,**extra):
        report["checks"].append({"name":name,"passed":bool(passed),**extra})
    try:
        data=args.vsix.read_bytes(); actual_sha=digest(data)
        report["sha256"]=actual_sha
        check("exact_finished_vsix_sha256",actual_sha==args.expected_sha256,expected=args.expected_sha256,actual=actual_sha)
        with zipfile.ZipFile(args.vsix) as archive:
            check("zip_crc_integrity",archive.testzip() is None)
            source_manifest=json.loads((editor/"package.json").read_text(encoding="utf-8"))
            package_manifest=json.loads(archive.read("extension/package.json"))
            check("manifest_json_logical_equality",package_manifest==source_manifest)
            report["vsce_added_package_json_keys"]=sorted(set(package_manifest)-set(source_manifest))
            expected={"extension.vsixmanifest","[Content_Types].xml","extension/package.json"}
            for filename in ("enter.js","enter.js.map","extension.js","extension.js.map","response.js","response.js.map","runtime.js","runtime.js.map"):
                relative="out/"+filename; member="extension/"+relative; expected.add(member)
                source_bytes=(editor/relative).read_bytes(); packaged=archive.read(member)
                check("compiled_byte_parity:"+relative,source_bytes==packaged,source_sha256=digest(source_bytes),packaged_sha256=digest(packaged))
            for filename in ("actual-enter-demo.gif","prefix-icon.png","real-enter-correction.jpg","real-manual-correction.jpg"):
                relative="assets/"+filename; member="extension/"+relative; expected.add(member)
                source_bytes=(editor/relative).read_bytes(); packaged=archive.read(member)
                check("asset_byte_parity:"+relative,source_bytes==packaged,source_sha256=digest(source_bytes),packaged_sha256=digest(packaged))
            for filename,member in (("README.md","readme.md"),("CHANGELOG.md","changelog.md"),("LICENSE.txt","LICENSE.txt"),("PRIVACY.md","PRIVACY.md"),("SUPPORT.md","SUPPORT.md")):
                expected.add("extension/"+member)
                source_text=(editor/filename).read_text(encoding="utf-8").replace("\r\n","\n")
                packaged=archive.read("extension/"+member).decode("utf-8").replace("\r\n","\n")
                if filename=="README.md":
                    report["vsce_readme_rewrites"]=README_TRANSFORMS
                    for relative,absolute in README_TRANSFORMS.items():
                        check("readme_relative_link_count:"+relative,source_text.count("("+relative+")")==1)
                        source_text=source_text.replace("("+relative+")","("+absolute+")")
                check("documentation_text_parity:"+filename,source_text==packaged,comparison="UTF-8 text; CRLF and LF treated equivalently")
            check("exact_archive_inventory",set(archive.namelist())==expected and len(archive.namelist())==len(expected),expected_entries=len(expected),actual_entries=len(archive.namelist()))
            identity=ET.fromstring(archive.read("extension.vsixmanifest")).find(".//{*}Identity")
            check("vsix_identity",identity is not None and identity.attrib.get("Id")==source_manifest["name"] and identity.attrib.get("Publisher")==source_manifest["publisher"] and identity.attrib.get("Version")==source_manifest["version"])
        report["passed"]=all(item["passed"] for item in report["checks"])
    except Exception as error:
        report["passed"]=False; report["error"]=str(error)
    report["counts"]={"pass":sum(item["passed"] for item in report["checks"]),"fail":sum(not item["passed"] for item in report["checks"]),"error":int("error" in report),"skip":0}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"passed":report["passed"],"counts":report["counts"],"output":str(args.output)},sort_keys=True))
    return 0 if report["passed"] else 1
if __name__=="__main__": raise SystemExit(main())
