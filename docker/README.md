# DiambraArena Container Images
- to build all images, run `make images`
- to push images, run `make push-images`

You can use a custom registries to pull base images and push final images to. To
see available options, run `make options`.

Run `make info` to see how to run the images.


## Image Hierarchy
````
 [ubuntu] [nvidia/cuda]
      \        /
       \      /
  <Dockerfile.base>
       /     \
   [base]  [base-cuda]
       \     /
     <Dockerfile>
       /     \
      /       \
  [arena]  [arena-cuda]


[] Image
<> Dockerfile
```
