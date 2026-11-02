#!/usr/bin/env python3
"""Fail-closed two-mode oracle for the immutable ModuleExportDecl subset."""
import json
from pathlib import Path
import sys

def compare(folder):
    from compare_differential import stable_semantic
    bad=[]
    matched={"diagnostics":0,"selected_semantic":0,"final_verification":0}
    for category,scenario,suffix in (
        ("differential","export_summary",""),
        ("verification","export-proof","verification-")
    ):
        snapshots={}
        for mode in ("fresh-semantic","immutable-export"):
            path=folder/f"{mode}-{suffix}{scenario}.json"
            if not path.is_file():
                bad.append([category,mode,"MISSING"])
                continue
            obj=json.loads(path.read_text())
            if obj.get("mode")!=mode or obj.get("scenario")!=scenario or len(obj.get("records",[]))!=4:
                bad.append([category,mode,"INVALID"])
                continue
            snapshots[mode]=obj["records"]
        if len(snapshots)!=2: continue
        for i,(a,b) in enumerate(zip(snapshots["fresh-semantic"],snapshots["immutable-export"])):
            if a.get("source")!=b.get("source") or a.get("revision")!=i or b.get("revision")!=i:
                bad.append([category,i,"INPUT_MISMATCH"])
                continue
            if category=="differential":
                if i==1 and not a.get("diagnostics"):
                    bad.append([category,i,"EXPECTED_TYPE_ERROR_NOT_TRIGGERED"])
                if not a.get("semantic") or not a["semantic"].get("definitions"):
                    bad.append([category,i,"UNEXERCISED_GOTO_DEFINITION"])
                if "diagnostics" not in a or "diagnostics" not in b:
                    bad.append([category,i,"MISSING_DIAGNOSTIC"])
                elif a["diagnostics"]!=b["diagnostics"]:
                    bad.append([category,i,"DIAGNOSTIC_DIFFERENCE"])
                else: matched["diagnostics"]+=1
                if not isinstance(a.get("semantic"),dict) or not isinstance(b.get("semantic"),dict):
                    bad.append([category,i,"MISSING_SEMANTIC"])
                elif stable_semantic(a["semantic"])!=stable_semantic(b["semantic"]):
                    bad.append([category,i,"SEMANTIC_DIFFERENCE"])
                else: matched["selected_semantic"]+=1
            else:
                aa=a.get("verification")
                bb=b.get("verification")
                if not isinstance(aa,list) or not isinstance(bb,list) or not aa or not bb:
                    bad.append([category,i,"MISSING_VERIFIER"])
                elif any(x.get("outcome") not in ("Correct","Error") for x in aa+bb):
                    bad.append([category,i,"NOT_TERMINAL"])
                elif aa!=bb:
                    bad.append([category,i,"VERIFIER_DIFFERENCE"])
                elif any(x["outcome"]=="Error" for x in aa)!=(i==1):
                    bad.append([category,i,"EXPECTED_PROOF_RESULT_DIFFERENT"])
                else: matched["final_verification"]+=1
    obj={"schema":"immutable-export-summary-v1","matched":matched,"errors":bad,
         "scope":"Export declaration only; immutable empty summary and current-compilation wrapper."}
    folder.mkdir(parents=True,exist_ok=True)
    (folder/"immutable-export-report.json").write_text(json.dumps(obj,indent=2)+"\n")
    print("Immutable export summary:",matched,"errors",len(bad))
    for row in bad[:15]: print("FAIL",row)
    return not bad and matched=={"diagnostics":4,"selected_semantic":4,"final_verification":4}

def selftest():
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        root=Path(d)
        for mode in ("fresh-semantic","immutable-export"):
            for category,scenario,suffix in (("diff","export_summary",""),("verify","export-proof","verification-")):
                records=[]
                for i in range(4):
                    r={"revision":i,"source":f"source-{i}"}
                    if category=="diff":r.update({"diagnostics":[{"message":"type mismatch"}] if i==1 else [],
                                                  "semantic":{"definitions":[{"uri":"file:///a.dfy"}],"hover":"int"}})
                    else:r["verification"]=[{"from":[0,0],"to":[0,3],"outcome":"Error" if i==1 else "Correct"}]
                    records.append(r)
                (root/f"{mode}-{suffix}{scenario}.json").write_text(json.dumps({"mode":mode,"scenario":scenario,"records":records}))
        assert compare(root)
        p=root/"immutable-export-verification-export-proof.json"
        obj=json.loads(p.read_text())
        obj["records"][1]["verification"][0]["outcome"]="Correct"
        p.write_text(json.dumps(obj))
        assert not compare(root)
        p.unlink()
        assert not compare(root)
    print("Immutable export comparator selftests PASS")

if __name__=="__main__":
    if len(sys.argv)!=2:raise SystemExit("usage: compare_immutable_export.py --selftest | <trace-folder>")
    if sys.argv[1]=="--selftest":selftest()
    elif not compare(Path(sys.argv[1])):sys.exit(1)
