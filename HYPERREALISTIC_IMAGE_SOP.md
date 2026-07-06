# Hyper-Realistic Image Prompt SOP

**AI Influencer Studio - Standard Operating Procedure**

The exact framework used to generate prompts that produce photorealistic,
non-AI-looking outputs from any reference image. Read this file whenever you
build the fictional UGC creator stills (operating rule 42 and UGC recipe step 4)
or any hyperrealistic still/character that must not look AI-generated. Keep
`SKILL.md` focused; this file carries the full prompt-construction method.

## How to apply this inside Super Video Maker

This SOP is a **prompt-construction framework**, not a new provider. Map it onto
the skill's existing tools:

- **OpenAI `gpt-image-2` (creator stills, `tools/image_provider.py`)** has no
  separate negative-prompt or ControlNet field. Fold sections 01-11 into the
  positive prompt text, and convert section 12's negative prompt into explicit
  "do NOT" / "avoid" clauses appended to the same prompt. When editing a
  licensed reference into a new fictional creator, pass `--input-fidelity high`
  so the skin texture and lens realism survive.
- **Seedance reference clips (`tools/fal_seedance_video.py`)** keep the same
  anti-AI vocabulary in the shot prompt; the character bible (`character_card.json`)
  stores the `visual_seed`, references, and negative prompts so every clip stays
  consistent.
- **ControlNet (section, below)** only applies on a ControlNet-capable backend
  (e.g. an SD/Seedance pose+depth pipeline). On `gpt-image-2` it is advisory —
  translate its constraints into plain prompt language ("preserve shoulder
  angle, keep the head turn").
- **Compliance gate (operating rules 40, 42, 49):** this framework makes a face
  look real, never to recreate a real person. The output must be a **new
  fictional creator** — do not preserve identity-level likeness of any reference
  person, and only use reference photos the user owns or has licensed.

Save the final JSON prompt next to the creator references in the job folder
(`assets/character/`) so every variant reuses the same locked description.

-----

## PART A: 12-PART FRAMEWORK

Every prompt is built from these 12 sections, in this order.

-----

### 01 - SUBJECT: Core Identity

**What it is:** The foundational description of who is in the image - age,
ethnicity, skin tone, build. This sets the entire baseline.

**How to write it:**

- Estimate age range in years (e.g. "mid-to-late 20s"), never just "young woman"
- Identify ethnicity or regional appearance (e.g. "Mediterranean", "Northern European", "Afro-Latina") - this controls bone structure, undertone, and hair texture
- Describe skin tone in two parts: the base tone (fair, light, medium, tan, dark) AND the undertone (peachy, olive, warm golden, cool pink, neutral)
- Note build only if it's visible and relevant - don't invent what you can't see

**✗ Too vague:** Young woman, tanned skin, dark hair.

**✓ Specific enough:** Young woman, mid-to-late 20s, warm medium-tan skin with golden-bronze undertone. British or American appearance with a heavily made-up glamour aesthetic.

-----

### 02 - FACIAL FEATURES: Skin

**What it is:** The most important anti-AI section. AI defaults to perfectly
smooth, pore-free, symmetrical skin. You must explicitly override this.

**How to write it:**

- Specify WHERE pores are visible (nose tip, cheeks, forehead T-zone) - not just "visible pores"
- Name specific imperfections: a mole, old acne mark, small blemish, slight redness around nostrils, under-eye shadow
- Describe the skin's surface quality: oily T-zone shine, dewy post-workout flush, periorbital hyperpigmentation, fine peach fuzz on cheeks
- For older subjects: name every aging feature - crow's feet, nasolabial folds, jowls, age spots, loose neck skin, vertical lip lines
- Add natural asymmetry note - one side of the face is never identical to the other

**✗ Too vague:** Natural skin texture, visible pores.

**✓ Specific enough:** Visible open pores across the nose and cheeks, slight natural oiliness on the T-zone, faint redness around the nostrils. A few minor blemishes or old acne marks visible on the cheek. Natural under-eye shadow - slight blue-purple tinge from tiredness, not heavily dark.

-----

### 03 - FACIAL FEATURES: Eyes, Brows, Nose, Mouth

**What it is:** Each facial feature needs specific detail. Generic descriptions
produce generic AI faces.

**How to write it:**

- **EYES:** Name the exact color (not just "brown" - "warm hazel-brown with darker limbal ring"). Describe iris texture. Note catchlight position by clock position (10 o'clock, 12 o'clock). Describe sclera - slight redness in corners, natural veining
- **EYEBROWS:** Thickness, color, groom level, stray hairs, whether they're filled or natural. Raised eyebrows for animated expressions.
- **NOSE:** Size, any bridge bump, tip shape, pore texture. If there's a nose ring or stud, describe it.
- **MOUTH:** Whether open or closed, lip texture (dry, glossy, fine vertical lines), tooth visibility (natural off-white, realistic spacing - never "perfect white teeth"). If mid-speech: which word position?
- **BEARD (male):** Growth density by zone (denser on chin, patchier on cheeks), color variation including gray hairs, follicle root visibility on neck

**✗ Too vague:** Brown eyes, natural makeup, open mouth.

**✓ Specific enough:** Dark brown eyes - deep rich brown iris with minimal visible texture due to dark pigmentation. Upper eyelid has a precise black liquid eyeliner - a clean wing extending slightly past the outer corner. Mouth slightly open mid-speech, teeth barely visible - natural off-white, natural spacing.

-----

### 04 - HAIR

**What it is:** Hair is one of the biggest AI giveaways. AI produces uniform,
plastic-looking hair. Every hair description must include texture variation.

**How to write it:**

- **Straight hair:** note multi-tonal color (lighter pieces at front, darker mid-lengths, warm honey-gold in areas). Note shine quality, flyaway hairs at the crown, any natural frizz
- **Curly hair:** use the curl type system (3a/3b/3c/4a/4b) - this controls the curl diameter. State whether air-dried or diffused. Note that curls vary in size across different areas of the head
- **Styled hair (bun, updo):** describe the messiness or neatness. Escaped strands, baby hairs, direction of the wrap. A "messy bun" must look like a real messy bun, not a round sphere
- **Wet/workout hair:** describe how sweat changes the color at the roots, how it flattens baby hairs
- Always mention: hairline quality, flyaways, where it falls relative to the shoulders/face, and the compression mark from any headband or hair tie

**✗ Too vague:** Long blonde hair, natural wave.

**✓ Specific enough:** Long straight blonde hair with face-framing highlights and subtle warm balayage. Multiple tones: lighter platinum pieces at the front, darker blonde through the mid-lengths, warm honey-gold in areas. A few flyaway hairs at the crown catching the light. Hair is clean but not blown out perfectly - natural and relaxed.

-----

### 05 - CLOTHING & ACCESSORIES

**What it is:** Clothing must be described at fabric level, not garment level.
The type of fabric and its behavior on the body is what makes clothing look real.

**How to write it:**

- Name the fabric type or weave: "French terry fleece with visible looped texture", "herringbone-weave with intersecting diagonal zigzag pattern", "smooth matte jersey stretch material"
- Describe how the fabric behaves: "natural horizontal stretch lines across the chest", "slight pilling at the neckline seam", "compression wrinkles at the sleeve bends"
- Describe wear level: is it new, worn-in, slightly faded, pilled?
- For jewelry: be photographically specific. Not "gold watch" - "rose gold luxury watch with octagonal bezel, integrated bracelet with alternating brushed and polished links, dark navy dial with gold indices." Not "necklace" - "Van Cleef Alhambra style, four white mother-of-pearl clover pendants on a delicate gold chain"
- Describe accessories that are worn vs held: seatbelt position, bag strap direction, how a jacket is draped

**✗ Too vague:** Gray blazer, white t-shirt, gold watch.

**✓ Specific enough:** Light gray herringbone-weave textured blazer - fabric texture clearly visible: intersecting diagonal zigzag pattern in light gray and off-white threads. Lapels sit naturally with slight compression wrinkles at the shoulder. Rose gold luxury watch - octagonal bezel design (Royal Oak AP style), integrated bracelet with alternating brushed and polished links, dark navy blue dial with subtle tapisserie pattern.

-----

### 06 - POSE & BODY LANGUAGE

**What it is:** Pose is more than position - it's weight distribution, tension,
and what the body is communicating. Natural poses have micro-imperfections.

**How to write it:**

- Describe weight distribution: which leg carries the weight, how the hip shifts, natural spine curve
- For seated poses: where the body leans (forward = engaged, back = relaxed), which arm supports weight, how the legs are positioned
- For hand gestures: describe the specific finger position. "Fingers spread naturally" vs "rigid fan" are completely different. Describe palm orientation.
- For the head: is it tilted, turned, angled up or down, and by how much? "Head tilted 15 degrees to the right" is more useful than "head tilted"
- Add body language interpretation: "the lean forward conveys that he is sharing something important" - this helps the model understand the emotional intent of the pose

**✗ Too vague:** Standing, hand on hip, looking at camera.

**✓ Specific enough:** Seated on a light gray sofa. Body angled slightly sideways, legs crossed - right leg over left - showing bare thigh below blazer hem. Both hands rest naturally on the crossed knee. Head faces the camera with chin slightly lowered. The posture of someone extremely comfortable on camera.

-----

### 07 - ENVIRONMENT & BACKGROUND

**What it is:** The background makes the image feel like a real place or a
rendered set. Every object in the background needs material and texture description.

**How to write it:**

- Describe wall surfaces: not just "gray wall" but "medium-light gray painted wall with slight texture from paint roller application - not perfectly smooth"
- Name specific background objects with detail: "a small ceramic plant pot with a trailing pothos" not "a plant", "old CRT-style television with slightly convex screen face" not "a TV"
- For bokeh/blurred backgrounds (podcast studios): describe the color mix and size variation of the bokeh circles - "varied bokeh balls - some large glowing circles, some smaller - predominantly purple-violet with pockets of red and warm pink"
- Describe surfaces the subject interacts with: the wood grain on the desk, the marble veining on the table, the fabric texture on the sofa
- Describe what the lighting does to the background: "warm amber glow from the LED strip illuminating the lower portions of the wooden slats"

**✗ Too vague:** Home office background with bookshelves.

**✓ Specific enough:** Warm-toned wooden open shelving unit - shelves stocked with a small ceramic plant pot with a trailing succulent, a vintage CRT-style television with a slightly convex screen, a framed print with orange and red tones leaning against the shelf. The shelving has a warm amber undertone from indirect light. A bright rectangular window glow bleeds in from the upper left, creating a soft diffused warm patch on the gray wall.

-----

### 08 - CAMERA & LENS

**What it is:** The camera perspective controls spatial relationships,
distortion, and compression. Getting this wrong makes an image feel wrong even
if everything else is right.

**How to write it:**

- Specify focal length equivalent: smartphone front cameras are 23-28mm (barrel distortion, nose appears larger). Portrait lenses are 85-105mm (compression, background gets closer). Standard lenses are 35-50mm (natural perspective).
- Name the angle: eye-level, slight low angle (looking up = power/authority), slightly high angle (looking down = candid/relatable)
- Describe specific distortion effects: "slight barrel distortion natural to front cameras: the nose appears very slightly larger, the ears slightly smaller" - this is what makes selfies look like selfies
- Specify framing crop precisely: "head and upper torso, cutting off just below chest level" rather than "medium close-up"
- Describe where the focus plane lands: "tack sharp on the eyes, slight softening toward the ears and background"

**✗ Too vague:** Close-up portrait shot.

**✓ Specific enough:** Smartphone front camera - 23-28mm equivalent. Slight wide-angle distortion natural to front cameras: the nose appears very slightly larger, the ears slightly smaller. The face has the typical slight barrel distortion of a selfie. Tack sharp on the eyes and eyeliner. Slight softening toward the ears and background.

-----

### 09 - LIGHTING

**What it is:** Lighting is described in terms of source, direction, quality,
color temperature, and the specific effects it creates on the subject and
environment.

**How to write it:**

- Name the light source type: natural window light, ring light, studio key light, fluorescent overhead, LED strip, golden hour sun, car sunroof
- Describe direction using clock positions for catchlights: "10-11 o'clock catchlight" tells the model exactly where the light is coming from
- Describe light quality: "large diffused source creating gentle wrap-around light" vs "harsh direct sun creating sharp shadows"
- List the shadows: where do they fall, how soft are their edges, what color are they?
- For mixed lighting: describe both sources and their color temperatures. "Warm 2800K overhead kitchen light on the subject, cool 6000K from the background window" - this creates the real-world color contrast that makes home videos look authentic
- Describe subsurface scattering effects on the skin: "realistic skin subsurface scattering - the nose tip glows slightly pink in the backlight"

**✗ Too vague:** Natural lighting, warm tones.

**✓ Specific enough:** Warm overhead kitchen light - top-down illumination: the forehead and top of the head are brighter, natural shadows fall under the brow ridge, under the nose, and under the chin. The cool blue light from the background window provides a contrasting ambient fill on the back wall - creating a color temperature contrast between warm foreground subject and cool background. Mixed: warm 2800-3200K overhead, cool 6000K background window.

-----

### 10 - MOOD & EXPRESSION

**What it is:** Expression and vibe instructions tell the model the emotional
intent. This affects micro-expressions, posture tension, and eye quality.

**How to write it:**

- Describe the specific expression with anatomical detail: "eyes wide open, eyebrows raised in an arc, mouth open mid-word" not just "surprised"
- Name the content creator archetype or context: "the kind of creator who talks about wellness, relationships, personal growth" - this adds context to the expression
- Distinguish between directed gaze (looking at the camera lens) and off-camera gaze (looking at the interviewer or host) - this completely changes the energy of the image
- For "mid-speech" expressions: specify where in the word - mid-word (mouth more open), between words (mouth slightly parted), end of sentence (mouth closing)
- Add body language interpretation as mood descriptor: "the posture of someone comfortably recording themselves at home"

**✗ Too vague:** Natural, candid expression.

**✓ Specific enough:** Genuinely animated - wide eyes raised in emphasis or surprise, mid-word expression, natural and unrehearsed. This is what someone looks like when making a strong point they're passionate about - not performed, not posed.

-----

### 11 - STYLE & REALISM: Anti-AI Notes

**What it is:** This is the most unique section of the SOP. You must explicitly
tell the model what AI typically gets wrong for THIS specific image and forbid it.

**How to write it:**

- Study the image and identify its 5-7 most distinctive details. Then write anti-AI notes for each one.
- Format: "Do not [thing AI always does]. The [element] must [what it should actually look like]."
- Common AI failures to always address: skin smoothing, uniform beard texture, symmetrical face, uniform hair curl pattern, blurred jewelry, smooth fabric texture (no weave), white perfect teeth, CGI background objects
- For specific elements: "The bun must NOT look like a uniform round AI shape - it must have messy escaped strands and visible hair direction." / "The watch face must have real dial details, not a blurred gold circle." / "The wooden slats must have visible wood grain on each individual slat."
- Reference what a real version of the content looks like: "Must look like a real frame grabbed from a 4K YouTube podcast video, similar aesthetic to Diary of a CEO or Lex Fridman"

**✗ Too vague:** Hyper-realistic, no filters.

**✓ Specific enough:** ANTI-AI NOTES: The face must not be symmetrical. The beard must have individual hairs, not a uniform texture. The watch face must have real dial details, not a blurred gold circle. The background bokeh must look like real colored studio lights, not a gradient blur. The blazer must have visible herringbone weave, not smooth CGI fabric.

-----

### 12 - NEGATIVE PROMPT

**What it is:** The negative prompt is a systematic list of everything to avoid.
It reinforces the anti-AI notes in a format that image models read directly.
(On `gpt-image-2`, which has no negative-prompt field, append these as explicit
"avoid / do NOT render" clauses at the end of the positive prompt.)

**How to write it:**

- Always include the core anti-AI negatives: "skin smoothing", "airbrushed", "beauty filters", "plastic skin", "anatomy normalization", "depth flattening"
- Add image-specific negatives based on what you wrote in the anti-AI notes
- For talking-head videos: always add "watermark", "text overlay", "captions", "play button overlay"
- For older subjects: add "age reduction", "youthened appearance", "reduced wrinkles"
- For specific accessories: "generic watch", "blurred watch", "generic jewelry", "blurred necklace"
- For hair: "uniform curl pattern", "uniform hair color", "smooth headband" (when the headband has texture)
- For expressions: "open eyes" (when eyes should be closed), "looking directly at camera" (when the gaze is off-camera)
- For environments: "studio backdrop", "rendered background", "CGI", "AI-generated props", "staged background"

**✗ Too vague:** No filters, realistic.

**✓ Specific enough:** ["skin smoothing", "airbrushed", "beauty filters", "plastic skin", "symmetrical face", "uniform beard texture", "blurred watch", "generic jewelry", "CGI blazer texture", "studio backdrop", "rendered background", "watermark", "text overlay", "depth flattening", "anatomy normalization"]

-----

## PART B: WORKFLOW

The exact sequence to follow each time you receive an image. Do not skip steps.

**Step 1 - Study the image for 30 seconds**
Before writing anything, look at every element. What is the setting? What is the
person wearing? What is the lighting doing? What makes this image feel real?

**Step 2 - Identify the 5 most distinctive details**
These are the things that would make the AI output look wrong if missed. The
watch brand, the specific curl type, the terry cloth headband texture, the LED
strip color on the wooden slats. Write these down first.

**Step 3 - Fill sections 01-10 in order**
Work through the framework section by section. Don't skip any section even if it
seems minimal - a short but specific note beats nothing.

**Step 4 - Write the Anti-AI Notes (section 11)**
Go back to your 5 distinctive details. For each one, write: "Do not [AI
failure]. The [element] must [real description]." This section is what separates
a good prompt from an AI-looking output.

**Step 5 - Build the negative prompt (section 12)**
Start with the core list. Add every item from your anti-AI notes as a negative.
Add any watermarks, text overlays, or interface elements to remove.

**Step 6 - Compress into JSON**
Format as a valid JSON object following the standard structure. Keep the key
names consistent across all prompts for easy parsing.

### Output Format

Always output as a valid JSON object. Use these exact top-level keys:

```json
{
  "subject": { "description": "", "facial_features": "", "hair": "", "build": "", "clothing": "", "accessories": "" },
  "pose": { "description": "", "weight_distribution": "", "body_language": "" },
  "environment": { "location": "", "background": "", "depth": "" },
  "props": { "microphone": "", "other": "" },
  "camera": { "shot_type": "", "framing": "", "lens": "", "focus_point": "" },
  "lighting": { "key_light": "", "fill": "", "catch_lights": "", "shadows": "", "color_temperature": "" },
  "mood_and_expression": { "vibe": "", "expression": "" },
  "style_and_realism": { "approach": "", "anti_ai_notes": "" },
  "colors_and_tone": { "palette": "", "contrast": "" },
  "quality": "",
  "aspect_ratio": "9:16",
  "controlnet": { "pose_control": {}, "depth_control": {} },
  "negative_prompt": []
}
```

### ControlNet - Include When the Backend Supports It

```json
"controlnet": {
  "pose_control": {
    "model": "DWPose",
    "weight": 0.95,
    "constraints": ["preserve shoulder angle", "preserve head turn", "..."]
  },
  "depth_control": {
    "model": "ZoeDepth",
    "weight": 0.85,
    "constraints": ["maintain subject-to-background separation", "..."]
  }
}
```

Increase pose_control weight to 1.0 when the pose has a critical gesture (hand
over face, arms raised, eyes closed). Add specific constraints for anything the
model might "normalize away." On `gpt-image-2` (no ControlNet field), translate
these constraints into plain prompt language instead.

-----

## PART C: ANTI-AI QUICK REFERENCE

The most common AI failures and exactly how to counter them. Use this as a
checklist after writing every prompt.

| Element | AI Default | Write Instead |
|---|---|---|
| Skin pores | Completely smooth, poreless | Name WHERE pores are: "visible open pores across the nose tip and upper cheeks" |
| Beard | Uniform fuzzy texture | "Individual hair strands, denser on chin, patchy on cheeks, a few gray hairs mixed in" |
| Hair (curly) | Uniform S-curl pattern, plastic shine | Curl type number (3c/4a), varied sizes, air-dried vs diffused, natural dull shine |
| Watch | Blurred gold circle | Brand silhouette + bezel shape + dial color + bracelet link detail |
| Jewelry/Necklace | Generic gold chain blur | Pendant shape, metal type, chain weight, pendant surface material (mother-of-pearl, etc.) |
| Fabric/Clothing | Smooth CGI material | Fabric type name + weave description + wear level + specific wrinkle locations |
| Background | Rendered set, perfect gradient | Paint texture on walls, specific objects with materials, what the light does to each surface |
| Teeth | Perfect white veneers | "Natural off-white, natural spacing, slightly imperfect - not veneered" |
| Face symmetry | Perfectly mirrored left and right | Explicitly note "natural facial asymmetry" in anti-AI notes |
| Eyeliner | Perfectly symmetrical digital lines | "Do not make the eyeliner perfectly symmetrical - a very slight natural human variance" |
| Bokeh/Podcast BG | Smooth gradient blur | "Varied bokeh circle sizes - some large, some smaller - specific color mix (purple, magenta, red)" |
| Old age skin | Age smoothed or reduced | Name every aging feature explicitly + add "age reduction" and "youthened appearance" to negative prompt |

### Universal Negative Prompt - Always Include These

skin smoothing - airbrushed - beauty filters - plastic skin - anatomy
normalization - depth flattening - symmetrical face - perfect teeth - uniform
beard texture - CGI texture - studio backdrop - rendered background - watermark -
text overlay - captions - play button

Then add image-specific negatives based on what you wrote in the anti-AI notes
for that particular image.
