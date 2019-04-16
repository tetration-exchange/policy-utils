from __future__ import print_function

from collections import defaultdict
from json import dumps
from operator import itemgetter
import argparse

from tetpyclient import RestClient


def get_workspaces():
    workspaces = rc.get("/applications")
    if workspaces.ok:
        return workspaces.json()
    else:
        quit("Could not retrieve workspaces because of " + workspaces.text.lower())


def get_workspace_detail(workspace):
    idx = workspace["id"]
    workspace = rc.get("/applications/{}/details".format(idx))
    return workspace.json()


def post_workspace(workspace):
    print("> Uploading merged workspace")

    # prepare for upload
    del workspace["id"]
    version = workspace["version"]
    split_version = version.split("v")
    incr = int(split_version[1]) + 1
    workspace["version"] = "v{}".format(incr)

    res = rc.post("/applications", json_body=dumps(workspace))
    if res.ok:
        print("> Success!")
    else:
        print("==== Error - Failed to save merged workspaces =====")
        quit(res.text)


def merge_workspaces(workspace0):
    print("> Merging workspaces")
    workspace1 = get_workspace_detail(workspace0)
    do_merge(workspace0, workspace1)
    post_workspace(workspace1)


def do_merge(w0, w1):
    """ 
        do_merge() performs an in-place merge of w0 into w1
    """
    policies_in_w0 = {"default_policies": {}, "absolute_policies": {}}

    for policy_type in policies_in_w0.keys():
        for policy in w0[policy_type]:
            actn = policy["action"]
            cons = policy["consumer_filter_id"]
            prov = policy["provider_filter_id"]
            policies_in_w0[policy_type]["{}+{}+{}".format(actn, cons, prov)] = {"policy": policy, "seen": False}

        for policy in w1[policy_type]:
            actn = policy["action"]
            cons = policy["consumer_filter_id"]
            prov = policy["provider_filter_id"]
            try:
                w0_policy = policies_in_w0[policy_type]["{}+{}+{}".format(actn, cons, prov)]
                w0_policy["seen"] = True
                policy["l4_params"] = merge_l4_params(w0_policy["policy"]["l4_params"], policy["l4_params"])

            # there is no old policy to merge with
            except KeyError:
                continue

        for policy in policies_in_w0[policy_type].values():
            if not policy["seen"]:
                w1[policy_type].append(policy["policy"])


def merge_l4_params(a, b):
    intervals = defaultdict(list)
    results = []
    non_port_based_protos = set()

    for p in a + b:
        if p.get("port", None):
            intervals[p["proto"]].append(p["port"])
        else:
            non_port_based_protos.add(p["proto"])

    for proto, ports in intervals.items():
        intervals[proto] = list(merge_intervals(ports))

    for proto, ports in intervals.items():
        for port_range in ports:
            results.append({"proto": proto, "port": port_range})
    for proto in non_port_based_protos:
        results.append({"proto": proto})

    return results


def merge_intervals(intervals):
    # https://codereview.stackexchange.com/questions/69242/merging-overlapping-intervals

    sorted_intervals = sorted(intervals, key=itemgetter(0))

    if not sorted_intervals:  # no intervals to merge
        return

    # low and high represent the bounds of the current run of merges
    low, high = sorted_intervals[0]

    for iv in sorted_intervals[1:]:
        if iv[0] <= high + 1:  # new interval overlaps current run
            high = max(high, iv[1])  # merge with the current run
        else:  # current run is over
            yield low, high  # yield accumulated interval
            low, high = iv  # start new run

    yield low, high  # end the final run


def main():
    global rc
    parser = argparse.ArgumentParser()
    parser.add_argument("url", help="URL of Tetration appliance")
    parser.add_argument("key", help="API key")
    parser.add_argument("secret", help="API secret")
    args = parser.parse_args()

    rc = RestClient(args.url, api_key=args.key, api_secret=args.secret)

    print("""
Tetration ADM Carry-over-Tool

    This app is designed to join the result of two ADM runs together

    To operate the app:

        0. Run ADM on the initial data set
        1. Select the workspace in this app, leave the app running
        2. Run ADM on the second data set
        3. Continue running the app to merge the two result sets

Available workspaces...
    """)
    workspaces = get_workspaces()

    for idx, ws in enumerate(workspaces):
        print("[{}] {}".format(idx, ws["name"]))

    while True:
        try:
            ws_idx = int(raw_input("\nChoose workspace to snapshot: "))
            saved_workspace = get_workspace_detail(workspaces[ws_idx])
            break
        except (KeyError, TypeError, IndexError, ValueError):
            print("Invalid choice")

    print("================================")
    print("")
    print("Snapshot created")
    print("")
    print("Re-run ADM. Press any key to begin merge with snapshot...")
    print("")
    raw_input("================================")

    merge_workspaces(saved_workspace)


if __name__ == "__main__":
    main()
