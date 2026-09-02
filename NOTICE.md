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

**Icons.** The UI icons are from [Tabler Icons](https://tabler.io/icons)
(MIT), inlined in `app.js` and `index.html`.

**TEMPO** is a sample brand created solely for this demo. It is not a real
product, company, or endorsement.

Third-party libraries used at runtime (loaded from their public CDNs, not
redistributed here): [three.js](https://threejs.org) (MIT) and the
[Clash Display](https://www.fontshare.com/fonts/clash-display) and
[Switzer](https://www.fontshare.com/fonts/switzer) typefaces (Fontshare license).
