
Enable DNS querries: https://cloud.google.com/knowledge/kb/enable-dns-queries-log-in-google-kubernetes-engine-000004855
in this example we'll enable it on all kube-dns pods since it a test cluster.
 gcloud compute instance-groups  list
gcloud compute instance-groups  list-instances gke-gke-iptables-debug-apps-593b445a-grp --zone australia-southeast1-a
