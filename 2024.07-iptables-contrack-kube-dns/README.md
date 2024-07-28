# Intro

This experiment explores `sessionAffinity` setting on a `iptables` powered kubernetes cluster. In particular how it affects load spread on kube-dns pods.

SessionAffinity is set by adding this section to a spec of an `svc`:
```yaml
  sessionAffinity: ClientIP
  sessionAffinityConfig:
    clientIP:
      timeoutSeconds: 20
```

# kube-dns

Enable DNS queries: https://cloud.google.com/knowledge/kb/enable-dns-queries-log-in-google-kubernetes-engine-000004855
in this example we'll enable it on all kube-dns pods since it a test cluster.

Use `dnsperf` to generate load on the kube-dns service. [example manifest](./dnsperf-cm-manifests.yaml)

List instances for `gcloud compute ssh`:

```sh
$ gcloud compute instance-groups list # pick a GROUP from here
$ gcloud compute instance-groups list-instances $GROUP --zone $ZONE
```

# Iptables

Example Service with 3 backend pods, without SessionAffinity set:

```sh
-A KUBE-SEP-6NWFNFWFHZHIJD3A -s 10.24.2.6/32 -m comment --comment "test/my-nginx" -j KUBE-MARK-MASQ
-A KUBE-SEP-6NWFNFWFHZHIJD3A -p tcp -m comment --comment "test/my-nginx" -m tcp -j DNAT --to-destination 10.24.2.6:80
-A KUBE-SEP-FSSMT4KUEAZYNFJI -s 10.24.1.8/32 -m comment --comment "test/my-nginx" -j KUBE-MARK-MASQ
-A KUBE-SEP-FSSMT4KUEAZYNFJI -p tcp -m comment --comment "test/my-nginx" -m tcp -j DNAT --to-destination 10.24.1.8:80
-A KUBE-SEP-LB56UD7DRAMFR6O4 -s 10.24.0.16/32 -m comment --comment "test/my-nginx" -j KUBE-MARK-MASQ
-A KUBE-SEP-LB56UD7DRAMFR6O4 -p tcp -m comment --comment "test/my-nginx" -m tcp -j DNAT --to-destination 10.24.0.16:80

-A KUBE-SERVICES -d 10.87.20.145/32 -p tcp -m comment --comment "test/my-nginx cluster IP" -m tcp --dport 80 -j KUBE-SVC-EWPKAXWJ2A225D7H
-A KUBE-SVC-EWPKAXWJ2A225D7H ! -s 10.24.0.0/24 -d 10.87.20.145/32 -p tcp -m comment --comment "test/my-nginx cluster IP" -m tcp --dport 80 -j KUBE-MARK-MASQ

-A KUBE-SVC-EWPKAXWJ2A225D7H -m comment --comment "test/my-nginx -> 10.24.0.16:80" -m statistic --mode random --probability 0.33333333349 -j KUBE-SEP-LB56UD7DRAMFR6O4
-A KUBE-SVC-EWPKAXWJ2A225D7H -m comment --comment "test/my-nginx -> 10.24.1.8:80" -m statistic --mode random --probability 0.50000000000 -j KUBE-SEP-FSSMT4KUEAZYNFJI
-A KUBE-SVC-EWPKAXWJ2A225D7H -m comment --comment "test/my-nginx -> 10.24.2.6:80" -j KUBE-SEP-6NWFNFWFHZHIJD3A
```

After `sessionAffinity` is set:

```sh
-A KUBE-SEP-6NWFNFWFHZHIJD3A -s 10.24.2.6/32 -m comment --comment "test/my-nginx" -j KUBE-MARK-MASQ
-A KUBE-SEP-6NWFNFWFHZHIJD3A -p tcp -m comment --comment "test/my-nginx" -m recent --set --name KUBE-SEP-6NWFNFWFHZHIJD3A --mask 255.255.255.255 --rsource -m tcp -j DNAT --to-destination 10.24.2.6:80
-A KUBE-SEP-FSSMT4KUEAZYNFJI -s 10.24.1.8/32 -m comment --comment "test/my-nginx" -j KUBE-MARK-MASQ
-A KUBE-SEP-FSSMT4KUEAZYNFJI -p tcp -m comment --comment "test/my-nginx" -m recent --set --name KUBE-SEP-FSSMT4KUEAZYNFJI --mask 255.255.255.255 --rsource -m tcp -j DNAT --to-destination 10.24.1.8:80
-A KUBE-SEP-LB56UD7DRAMFR6O4 -s 10.24.0.16/32 -m comment --comment "test/my-nginx" -j KUBE-MARK-MASQ
-A KUBE-SEP-LB56UD7DRAMFR6O4 -p tcp -m comment --comment "test/my-nginx" -m recent --set --name KUBE-SEP-LB56UD7DRAMFR6O4 --mask 255.255.255.255 --rsource -m tcp -j DNAT --to-destination 10.24.0.16:80

-A KUBE-SERVICES -d 10.87.20.145/32 -p tcp -m comment --comment "test/my-nginx cluster IP" -m tcp --dport 80 -j KUBE-SVC-EWPKAXWJ2A225D7H
-A KUBE-SVC-EWPKAXWJ2A225D7H ! -s 10.24.0.0/24 -d 10.87.20.145/32 -p tcp -m comment --comment "test/my-nginx cluster IP" -m tcp --dport 80 -j KUBE-MARK-MASQ

-A KUBE-SVC-EWPKAXWJ2A225D7H -m comment --comment "test/my-nginx -> 10.24.0.16:80" -m recent --rcheck --seconds 20 --reap --name KUBE-SEP-LB56UD7DRAMFR6O4 --mask 255.255.255.255 --rsource -j KUBE-SEP-LB56UD7DRAMFR6O4
-A KUBE-SVC-EWPKAXWJ2A225D7H -m comment --comment "test/my-nginx -> 10.24.1.8:80" -m recent --rcheck --seconds 20 --reap --name KUBE-SEP-FSSMT4KUEAZYNFJI --mask 255.255.255.255 --rsource -j KUBE-SEP-FSSMT4KUEAZYNFJI
-A KUBE-SVC-EWPKAXWJ2A225D7H -m comment --comment "test/my-nginx -> 10.24.2.6:80" -m recent --rcheck --seconds 20 --reap --name KUBE-SEP-6NWFNFWFHZHIJD3A --mask 255.255.255.255 --rsource -j KUBE-SEP-6NWFNFWFHZHIJD3A

-A KUBE-SVC-EWPKAXWJ2A225D7H -m comment --comment "test/my-nginx -> 10.24.0.16:80" -m statistic --mode random --probability 0.33333333349 -j KUBE-SEP-LB56UD7DRAMFR6O4
-A KUBE-SVC-EWPKAXWJ2A225D7H -m comment --comment "test/my-nginx -> 10.24.1.8:80" -m statistic --mode random --probability 0.50000000000 -j KUBE-SEP-FSSMT4KUEAZYNFJI
-A KUBE-SVC-EWPKAXWJ2A225D7H -m comment --comment "test/my-nginx -> 10.24.2.6:80" -j KUBE-SEP-6NWFNFWFHZHIJD3A
```

notice this bit is added `-m recent --set --name KUBE-SEP-LB56UD7DRAMFR6O4 --mask 255.255.255.255 --rsource`  and then before the round robin section we have this entry for each pod: 
```sh
-A KUBE-SVC-EWPKAXWJ2A225D7H -m comment --comment "test/my-nginx -> 10.24.0.16:80" -m recent --rcheck --seconds 20 --reap --name KUBE-SEP-LB56UD7DRAMFR6O4 --mask 255.255.255.255 --rsource -j KUBE-SEP-LB56UD7DRAMFR6O4
```

[Sample dump of contrack table](./dumps/conntrack-table.txt)

# Conclusion

Counterintuitevily, in a large cluster setting `sessionAffinity` helped to spread the load on the kube-dns pods evenly.
This is yet to be proven, but I belive this is due to reducing number of entries in conntrack table. Before the affinity every new request from src-podA will randomly choose 1 of N backend kube-dns pods.
Each of these connections will create an entry in conntrack table. With Affinity each consequent request from the same source pod will fall into the same entry for the duration of the affinity.

## Potential risks

* If a destination pod becomes unhealthy, but not yet taken out of service by the readiness probe, is there a risk that source pod will keep trying to connect to this pod or are their automatic fallbacks that will route it to a new pod?

* rollout of the destination service?

* Will it co-exist nicely with `Topology Aware Routing` and `Traffic Distribution`?