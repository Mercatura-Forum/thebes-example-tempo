# NOTICE

The source code, styling, logo, and all TEMPO brand artwork in this
repository — including the generated can labels (`assets/label_*.png`) and the
static can renders (`assets/can_*.png`) — are original works, released under the
MIT License (see [LICENSE](LICENSE)).

**3D model.** The can mesh in `assets/tempo-can.glb` is derived from a generic
aluminium soft-drink-can model (a commodity cylinder shape). It has been
re-textured for this project: any label artwork from the original source was
discarded and replaced entirely with original TEMPO artwork, and the top/bottom
were reassigned to a bare metal material. The underlying mesh geometry is a
common commodity shape and is included here only to run the demonstration; it
carries no third-party branding.

**Splash.** The frozen-fluid splash in `assets/splash.glb` is derived from
["Water Splash"](https://sketchfab.com/3d-models/water-splash-b203c05bf0c44817ab85187237fefd53)
by [Asfandyar Hesami](https://sketchfab.com/allkhanan1), licensed under
[CC-BY-4.0](http://creativecommons.org/licenses/by/4.0/). Modifications: the
simulation's stand-in body and baked textures were removed, the three splash
meshes were decimated and rescaled onto the TEMPO can's frame
(`src-model/tools/build_splash.py`), and materials are replaced at runtime.

## Cairo street (section 05)

The walkable street scene (`assets/street/street.glb`, `runner.glb`,
`poster.webp`) is kitbashed from license-verified external models. Every asset
below was re-tinted to the TEMPO palette, decimated, kitbash-placed and
draco-recompressed by `src-model/tools/build_street.py` /
`build_runner.py` — these modifications apply to every entry.

CC-BY 4.0 assets ([license](http://creativecommons.org/licenses/by/4.0/)):

- ["Arab House(low poly)"](https://sketchfab.com/3d-models/arab-houselow-poly-a49323aa1e0f450db9ff8b813864379f)
  by [Legorook](https://sketchfab.com/Legorook) — the hero facade (also: bundled
  ground plane removed, footprint squeezed to the site slot).
- ["The Minaret of Samarra, Iraq"](https://sketchfab.com/3d-models/the-minaret-of-samarra-iraq-d8ebe7c756f2414bb70768d936f2d137)
  by [Chenzoss](https://sketchfab.com/Chenzoss) — the skyline minaret.
- ["Tuk Tuk Auto Rikshaw Lowpoly"](https://sketchfab.com/3d-models/tuk-tuk-auto-rikshaw-lowpoly-2124df89548644278c6d4d1b1b0ad92a)
  by [maanzart](https://sketchfab.com/maanzart) — parked on the left curb.
- ["Low Poly Delivery Electric Scooter"](https://sketchfab.com/3d-models/low-poly-delivery-electric-scooter-16a3330edde14cb7b56626ede007067f)
  by [ramdom_sp](https://sketchfab.com/spartanmelon) — leaning by the shopfront.
- ["Monoblok low poly Garden Chair plastic"](https://sketchfab.com/3d-models/monoblok-low-poly-garden-chair-plastic-898f2dc1ef244f1b8785fbb508b6a339)
  by [The Latest Shit](https://sketchfab.com/thelatestshit) — the ahwa chairs (×2).

CC0 assets (no attribution required — credited with thanks): the runner body
and gaits from [KayKit Adventurers](https://kaylousberg.itch.io/kaykit-adventurers)
and [KayKit Character Animations](https://kaylousberg.itch.io/kaykit-character-animations)
by Kay Lousberg (plus the Crate of Potatoes); the Can Fridge, Cat, Crate and
Pot by [Quaternius](https://poly.pizza); the Round Table by
[Kenney](https://poly.pizza/m/AXbvcMDC8j) (the Kenney logo is trademarked and
is not used); the Wooden Sign by [iPoly3D](https://poly.pizza/m/AsEgIQcQfw).

The Arabic sign lettering is set in [Amiri](https://github.com/aliftype/amiri)
by Khaled Hosny (Alif Type), licensed under the
[SIL Open Font License 1.1](https://openfontlicense.org); the font renders to
baked textures only and is not redistributed as a font file by the site.

**Icons.** The UI icons are from [Tabler Icons](https://tabler.io/icons)
(MIT), inlined in `index.html`.

**Thebes SDK runtime.** `sdk/boundary.js` and `sdk/passkey.js` are unmodified
copies of the browser runtime from the
[Thebes SDK](https://github.com/Mercatura-Forum/thebes-sdk) (commit `9337c0c`),
licensed under Apache-2.0.

**thebes-lib.** `motoko/thebes-lib/` is an unmodified vendored copy of
[thebes-lib](https://github.com/Mercatura-Forum/thebes-lib) (commit `15aaa13`),
the standard Motoko backend library for Thebes apps, licensed under Apache-2.0
(its LICENSE and NOTICE travel with it).

**TEMPO** is a sample brand created solely for this demo. It is not a real
product, company, or endorsement.

Third-party libraries used at runtime (loaded from their public CDNs, not
redistributed here): [three.js](https://threejs.org) (MIT) and the
[Clash Display](https://www.fontshare.com/fonts/clash-display) and
[Switzer](https://www.fontshare.com/fonts/switzer) typefaces (Fontshare license).
