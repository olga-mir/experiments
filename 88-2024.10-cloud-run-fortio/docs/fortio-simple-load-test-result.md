
```
Starting at 150 qps with 10 thread(s) [gomax 2] for 1m0s : 900 calls each (total 9000)
Ended after 1m0.240870773s : 2512 calls. qps=41.699
Sleep times : count 2502 avg 0.018504634 +/- 0.01183 min 6.2985e-05 max 0.065658394 sum 46.2985955
Aggregated Function Time : count 2512 avg 0.22030882 +/- 0.1247 min 0.176474131 max 0.751680064 sum 553.415761
# range, mid point, percentile, count
>= 0.176474 <= 0.2 , 0.188237 , 86.54, 2174
> 0.2 <= 0.3 , 0.25 , 93.43, 173
> 0.3 <= 0.4 , 0.35 , 94.23, 20
> 0.4 <= 0.5 , 0.45 , 94.63, 10
> 0.5 <= 0.75 , 0.625 , 95.50, 22
> 0.75 <= 0.75168 , 0.75084 , 100.00, 113
# target 50% 0.190061
# target 75% 0.19686
# target 90% 0.250173
# target 99% 0.751307
# target 99.9% 0.751643
Error cases : count 113 avg 0.75073998 +/- 0.0003486 min 0.750118791 max 0.751680064 sum 84.833618
# range, mid point, percentile, count
>= 0.750119 <= 0.75168 , 0.750899 , 100.00, 113
# target 50% 0.750892
# target 75% 0.751286
# target 90% 0.751523
# target 99% 0.751664
# target 99.9% 0.751678
# Socket and IP used for each connection:
[0]   5 socket used, resolved to [216.239.36.53:443 (3), 216.239.34.53:443 (1), 216.239.38.53:443 (1)], connection timing : count 5 avg 0.0019781072 +/- 0.000409 min 0.001632457 max 0.002772944 sum 0.009890536
[1]   7 socket used, resolved to [216.239.36.53:443 (3), 216.239.38.53:443 (1), 216.239.32.53:443 (3)], connection timing : count 7 avg 0.00190645 +/- 0.0004908 min 0.001537258 max 0.002906682 sum 0.01334515
[2]  35 socket used, resolved to [216.239.34.53:443 (10), 216.239.38.53:443 (6), 216.239.36.53:443 (11), 216.239.32.53:443 (8)], connection timing : count 35 avg 0.0018211219 +/- 0.0003056 min 0.001312454 max 0.003061024 sum 0.063739265
[3]  12 socket used, resolved to [216.239.36.53:443 (6), 216.239.34.53:443 (3), 216.239.32.53:443 (1), 216.239.38.53:443 (2)], connection timing : count 12 avg 0.0015411552 +/- 0.0002033 min 0.001275263 max 0.001846066 sum 0.018493863
[4]  14 socket used, resolved to [216.239.36.53:443 (4), 216.239.34.53:443 (3), 216.239.38.53:443 (4), 216.239.32.53:443 (3)], connection timing : count 14 avg 0.001744251 +/- 0.0001765 min 0.001365833 max 0.002032603 sum 0.024419514
[5]  19 socket used, resolved to [216.239.36.53:443 (2), 216.239.38.53:443 (6), 216.239.34.53:443 (7), 216.239.32.53:443 (4)], connection timing : count 19 avg 0.0016831776 +/- 0.000312 min 0.001266349 max 0.002556946 sum 0.031980374
[6]   6 socket used, resolved to [216.239.36.53:443 (1), 216.239.32.53:443 (2), 216.239.38.53:443 (2), 216.239.34.53:443 (1)], connection timing : count 6 avg 0.0016720573 +/- 0.0004374 min 0.0013278 max 0.002624673 sum 0.010032344
[7]  12 socket used, resolved to [216.239.36.53:443 (5), 216.239.32.53:443 (5), 216.239.38.53:443 (1), 216.239.34.53:443 (1)], connection timing : count 12 avg 0.0016233232 +/- 0.0004615 min 0.001119998 max 0.002984806 sum 0.019479879
[8]  17 socket used, resolved to [216.239.38.53:443 (7), 216.239.32.53:443 (3), 216.239.36.53:443 (4), 216.239.34.53:443 (3)], connection timing : count 17 avg 0.0016383654 +/- 0.0002683 min 0.001240304 max 0.002290558 sum 0.027852212
[9]   5 socket used, resolved to [216.239.36.53:443 (1), 216.239.34.53:443 (2), 216.239.38.53:443 (1), 216.239.32.53:443 (1)], connection timing : count 5 avg 0.001980038 +/- 0.0004124 min 0.001627195 max 0.00268271 sum 0.00990019
Connection time histogram (s) : count 132 avg 0.0017358585 +/- 0.0003508 min 0.001119998 max 0.003061024 sum 0.229133327
# range, mid point, percentile, count
>= 0.00112 <= 0.0012 , 0.00116 , 0.76, 1
> 0.0012 <= 0.0014 , 0.0013 , 15.91, 20
> 0.0014 <= 0.0016 , 0.0015 , 34.85, 25
> 0.0016 <= 0.0018 , 0.0017 , 68.18, 44
> 0.0018 <= 0.002 , 0.0019 , 84.85, 22
> 0.002 <= 0.0025 , 0.00225 , 94.70, 13
> 0.0025 <= 0.003 , 0.00275 , 99.24, 6
> 0.003 <= 0.00306102 , 0.00303051 , 100.00, 1
# target 50% 0.00169091
# target 75% 0.00188182
# target 90% 0.00226154
# target 99% 0.00297333
# target 99.9% 0.00305297
Sockets used: 132 (for perfect keepalive, would be 10)
Uniform: true, Jitter: false, Catchup allowed: false
IP addresses distribution:
216.239.36.53:443: 40
216.239.34.53:443: 31
216.239.38.53:443: 31
216.239.32.53:443: 30
Code  -1 : 113 (4.5 %)
Code 200 : 2399 (95.5 %)
Response Header Sizes : count 2512 avg 0 +/- 0 min 0 max 0 sum 0
Response Body/Total Sizes : count 2512 avg 82.086385 +/- 18.03 min -1 max 86 sum 206201
Saved result to data/2024-12-02-072055_3_Fortio.json (graph link)
All done 2512 calls 220.309 ms avg, 41.7 qps
```
