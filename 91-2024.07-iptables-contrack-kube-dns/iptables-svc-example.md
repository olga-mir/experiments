
## Cluster State


```bash
% k get po -o wide
NAME                       READY   STATUS    RESTARTS   AGE   IP           NODE                  NOMINATED NODE   READINESS GATES
httpd-a-77b68dd7bd-57lrn   1/1     Running   0          63m   10.0.0.59    i-0d0b284d026cd64e2   <none>           <none>
httpd-a-77b68dd7bd-5h2qm   1/1     Running   0          41m   10.0.2.21    i-046430dafbe0a699c   <none>           <none>
httpd-a-77b68dd7bd-fn4np   1/1     Running   0          41m   10.0.2.100   i-046430dafbe0a699c   <none>           <none>
httpd-a-77b68dd7bd-ggblz   1/1     Running   0          41m   10.0.0.218   i-0d0b284d026cd64e2   <none>           <none>
httpd-a-77b68dd7bd-hf6mw   1/1     Running   0          63m   10.0.0.86    i-0d0b284d026cd64e2   <none>           <none>
```

## On node i-046430dafbe0a699c

```
Chain KUBE-SEP-VLI4ZIVDKI55EGCU (1 references)
target     prot opt source               destination
KUBE-MARK-MASQ  all  --  ip-10-0-2-100.ap-southeast-2.compute.internal  anywhere             /* httpd/httpd-a */
DNAT       tcp  --  anywhere             anywhere             /* httpd/httpd-a */ tcp to:10.0.2.100:8080

Chain KUBE-SEP-N3OA6LSYBBMSN7OT (1 references)
target     prot opt source               destination
KUBE-MARK-MASQ  all  --  ip-10-0-0-86.ap-southeast-2.compute.internal  anywhere             /* httpd/httpd-a */
DNAT       tcp  --  anywhere             anywhere             /* httpd/httpd-a */ tcp to:10.0.0.86:8080

Chain KUBE-SERVICES (2 references)
target     prot opt source               destination
...
KUBE-SVC-DDHLYWQIRV3Z4PSQ  tcp  --  anywhere             100.67.170.97        /* httpd/httpd-a cluster IP */ tcp dpt:http-alt
...

Chain KUBE-SVC-DDHLYWQIRV3Z4PSQ (1 references)
target     prot opt source               destination
KUBE-MARK-MASQ  tcp  -- !100.96.0.0/11        100.67.170.97        /* httpd/httpd-a cluster IP */ tcp dpt:http-alt
KUBE-SEP-K5KVGXV2MLWQ6QSS  all  --  anywhere             anywhere             /* httpd/httpd-a -> 10.0.0.218:8080 */ statistic mode random probability 0.20000000019
KUBE-SEP-NW2L6FSWLMQFGNAK  all  --  anywhere             anywhere             /* httpd/httpd-a -> 10.0.0.59:8080 */ statistic mode random probability 0.25000000000
KUBE-SEP-N3OA6LSYBBMSN7OT  all  --  anywhere             anywhere             /* httpd/httpd-a -> 10.0.0.86:8080 */ statistic mode random probability 0.33333333349
KUBE-SEP-VLI4ZIVDKI55EGCU  all  --  anywhere             anywhere             /* httpd/httpd-a -> 10.0.2.100:8080 */ statistic mode random probability 0.50000000000
KUBE-SEP-PIRRB47BRJGFNBV7  all  --  anywhere             anywhere             /* httpd/httpd-a -> 10.0.2.21:8080 */
```
