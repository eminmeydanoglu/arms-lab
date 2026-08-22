# SO-101 third-party assets

The simulator will vendor a pinned copy of the SO-101 URDF and mesh assets from TheRobotStudio/SO-ARM100 rather than downloading assets at runtime.

Do not copy an unpinned `main` snapshot here. When assets are added, record:

- upstream repository URL
- exact upstream commit SHA
- copied file list
- upstream license/attribution
- any collision-mesh adaptations made locally

The first implementation task in `FIRST_STEPS.md` is to populate this directory and add an asset integrity test.
