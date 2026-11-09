#!/usr/bin/env python3
"""Fail-closed two-mode oracle for the immutable ModuleExportDecl subset."""
import json
import re
from pathlib import Path
import sys

def compare(folder):
    from compare_differential import stable_semantic
    bad=[]
    matched={"diagnostics":0,"selected_semantic":0,"final_verification":0}
    for category,scenario,suffix in (
        ("differential","export_summary",""),
        ("differential","negative_alias",""),
        ("differential","provider_shadowing",""),
        ("verification","export-proof","verification-")
    ):
        snapshots={}
        for mode in ("fresh-semantic","immutable-export"):
            path=folder/f"{mode}-{suffix}{scenario}.json"
            if not path.is_file():
                bad.append([category,mode,"MISSING"])
                continue
            obj=json.loads(path.read_text())
            expected_count = 3 if scenario == "provider_shadowing" else 4
            if obj.get("mode")!=mode or obj.get("scenario")!=scenario or len(obj.get("records",[]))!=expected_count:
                bad.append([category,mode,"INVALID"])
                continue
            snapshots[mode]=obj["records"]
        if len(snapshots)!=2: continue
        for i,(a,b) in enumerate(zip(snapshots["fresh-semantic"],snapshots["immutable-export"])):
            if a.get("source")!=b.get("source") or a.get("revision")!=i or b.get("revision")!=i:
                bad.append([category,i,"INPUT_MISMATCH"])
                continue
            if category=="differential":
                if scenario=="export_summary" and i==1 and not a.get("diagnostics"):
                    bad.append([category,i,"EXPECTED_TYPE_ERROR_NOT_TRIGGERED"])
                if scenario=="export_summary" and (not a.get("semantic") or not a["semantic"].get("definitions")):
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
                if scenario=="negative_alias":
                    expected_diagnostics=(1,0,1,0)
                    expected_semantic=(False,True,False,True)  # binding presence
                    if len(a.get("diagnostics",[]))!=expected_diagnostics[i]:
                        bad.append([category,i,"UNEXPECTED_NEGATIVE_DIAGNOSTIC_COUNT"])
                    semantic=a.get("semantic")
                    candidate=b.get("semantic")
                    for label,query in (("fresh",semantic),("immutable",candidate)):
                        if not isinstance(query,dict):
                            bad.append([category,i,"MISSING_NEGATIVE_SEMANTIC_QUERY",label])
                            continue
                        resolved=bool(query.get("definitions"))
                        if resolved!=expected_semantic[i]:
                            bad.append([category,i,"UNEXPECTED_NEGATIVE_BINDING_PRESENCE",label])
                    if expected_semantic[i] and isinstance(semantic,dict):
                        import re
                        if (not semantic.get("definitions") or
                                not isinstance(semantic.get("hover"),str) or
                                not re.search(r"\bfunction\s+Missing\s*\(\s*\)\s*:\s*int\b",semantic["hover"])):
                            bad.append([category,i,"INCOMPLETE_NEGATIVE_SEMANTIC"])
                        if (not isinstance(candidate,dict) or
                                not re.search(r"\bfunction\s+Missing\s*\(\s*\)\s*:\s*int\b",
                                              candidate.get("hover", ""))):
                            bad.append([category,i,"INCOMPLETE_CANDIDATE_NEGATIVE_SEMANTIC"])
                if scenario=="provider_shadowing":
                    consumer="module Consumer { import opened ProviderA\n import opened ProviderB\n function Result(): int { Value() } }"
                    if not a.get("source", "").rstrip().endswith(consumer):
                        bad.append([category,i,"CONSUMER_SOURCE_CHANGED"])
                    expected_ranges=(([0,28],[0,33]) if i in (0,2) else (None,None))
                    ambiguous=any("ambiguously refers" in d.get("message","") and
                                  "Value" in d.get("message","") for d in a.get("diagnostics",[]))
                    if ambiguous != (i==1):
                        bad.append([category,i,"UNEXPECTED_AMBIGUITY_OUTCOME"])
                    for label,query in (("fresh",a.get("semantic")),("safe",b.get("semantic"))):
                        definitions=query.get("definitions",[]) if isinstance(query,dict) else []
                        if i==1:
                            if definitions:
                                bad.append([category,i,"AMBIGUOUS_NAME_HAS_DEFINITION",label])
                        elif (len(definitions)!=1 or
                              not definitions[0].get("uri","").endswith("research-differential-provider_shadowing.dfy") or
                              definitions[0].get("from")!=expected_ranges[0] or
                              definitions[0].get("to")!=expected_ranges[1]):
                            bad.append([category,i,"WRONG_PROVIDER_BINDING_TARGET",label])
                        elif not re.search(
                                r"\bfunction\s+Value\s*\(\s*\)\s*:\s*int\b",
                                query.get("hover", "")):
                            bad.append([category,i,"INCOMPLETE_PROVIDER_BINDING_SIGNATURE",label])
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
    return not bad and matched=={"diagnostics":11,"selected_semantic":11,"final_verification":4}

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
            alias_records=[]
            for i in range(4):
                semantic=({"definitions":[{"uri":"file:///provider.dfy"}],
                           "hover":"```dafny\nfunction Missing(): int\n```"}
                          if i in (1,3) else {"definitions":[],"hover":None})
                alias_records.append({"revision":i,"source":f"alias-source-{i}",
                                      "diagnostics":[{"message":"unresolved"}] if i in (0,2) else [],
                                      "semantic":semantic})
            (root/f"{mode}-negative_alias.json").write_text(json.dumps(
                {"mode":mode,"scenario":"negative_alias","records":alias_records}))
            shadow_records=[]
            for i in range(3):
                source=("module ProviderA { function Value(): int { 1 } }\nmodule ProviderB { }\n"
                        "module Consumer { import opened ProviderA\n import opened ProviderB\n function Result(): int { Value() } }\n")
                if i==1:
                    source=source.replace("module ProviderB { }",
                                          "module ProviderB { function Value(): int { 2 } }")
                shadow_records.append({"revision":i,"source":source,
                    "diagnostics":[{"message":"The name Value ambiguously refers to ProviderA, ProviderB"}] if i==1 else [],
                    "semantic":{"definitions":[] if i==1 else [{"uri":"file:///research-differential-provider_shadowing.dfy","from":[0,28],"to":[0,33]}],
                                "hover":None if i==1 else "```dafny\nfunction Value(): int\n```"}})
            (root/f"{mode}-provider_shadowing.json").write_text(json.dumps(
                {"mode":mode,"scenario":"provider_shadowing","records":shadow_records}))
        assert compare(root)
        p=root/"immutable-export-provider_shadowing.json"
        obj=json.loads(p.read_text())
        obj["records"][2]["semantic"]["definitions"][0]["from"]=[1,28]
        p.write_text(json.dumps(obj))
        assert not compare(root)
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
