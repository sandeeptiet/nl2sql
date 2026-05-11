# Step 1 — Create SA and grant anyuid
oc create serviceaccount phpmyadmin-sa -n nl2sql
oc adm policy add-scc-to-user anyuid -z phpmyadmin-sa -n nl2sql

# Step 2 — Apply the manifest
oc apply -f deployment/k8s/phpmyadmin/deployment.yaml   # adjust path to your file

# Step 3 — Watch it come up
oc get pods -n nl2sql -w

# Step 4 Get the URL
oc get route phpmyadmin -n nl2sql
# Open: https://phpmyadmin-nl2sql.apps-crc.testing

Login with your MySQL root credentials from nl2sql-secret. This approach is much cleaner and avoids all the Helm/Bitnami SCC headaches.