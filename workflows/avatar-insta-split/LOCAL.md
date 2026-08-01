# LOCAL notes — avatar-insta-split (Borja)  (do NOT publish)

Default presenter for this machine is **Borja Obeso Avatar 5 v1** (cap + podcast
mic). The ids are already set in the project `.env`, so `gen_avatar.py` picks them
up automatically — no flags needed:

```
HEYGEN_AVATAR_ID=731c0983f6664e86857ea60cdb87ba42   # Borja Obeso Avatar 5 v1
HEYGEN_VOICE_ID=028e8a5d94bd4fceaf2ffe5e51cc27cb     # Borja Obeso Avatar 5 v1 voice
```

Notes:
- This avatar renders **letterboxed** (content band ≈ 1080x608 @ y=656); the
  build's auto band-detect handles it, so the split layout stays full (no
  fullscreen hook/CTA), which frames the cap + mic best.
- Other Borja avatars on the account: `519ae1ac…` (clean bright room, no mic) is
  the closest match to real selfie footage if you want a different look.
- HeyGen API generation draws from the **API credit** pool (separate from the web
  studio plan). Top up API credits if you hit `MOVIO_PAYMENT_INSUFFICIENT_CREDIT`.

This file is git-ignored in the public repo; keep avatar ids out of anything pushed.
