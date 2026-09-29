# GitLab CI with Harbor

The GitLab pipeline uses `harbor.keti.xrds.kr/physical_ai_hub/fr3-wave-runtime`.
On the default branch it pushes only the runtime image: first as
`candidate-<commit SHA>` for a smoke test, then as `runtime-<commit SHA>` after
that test passes. The publish job
copies the tested artifact with digest preservation instead of rebuilding it.

1. In Harbor project `physical_ai_hub`, create a project robot account with
   **Pull Repository** and **Push Repository** permissions. Keep its generated
   secret in a password manager; do not commit it.
2. In GitLab project **Settings > CI/CD > Variables**, add `DOCKER_AUTH_CONFIG`
   as a masked, protected variable. Protect the default branch as well. Its
   value is a single-line Docker auth JSON object:

   ```json
   {"auths":{"harbor.keti.xrds.kr":{"auth":"BASE64_OF_ROBOT_USERNAME_COLON_SECRET"}}}
   ```

   Generate the `auth` field locally with
   `printf '%s:%s' "$ROBOT_USERNAME" "$ROBOT_SECRET" | base64 | tr -d '\n'`.
   Use the complete Harbor robot account username, including its prefix.
   The runner needs this variable **before** the smoke-test job starts so it
   can pull the private candidate image.
3. Ensure the Kubernetes runner can resolve and trust the Harbor HTTPS host.
   Its rootless BuildKit job must permit user namespaces and mount operations.
   The runner's build PVC also has to bind and attach; Harbor does not replace
   that local build storage.

Other branches run the ROS tests without Harbor credentials or image pushes.
Candidate tags should be covered by a Harbor retention policy after they are no
longer needed. Run the pipeline after the variable and runner prerequisites are
ready.
