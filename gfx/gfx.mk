# Mesa (panfrost) EGL/GLES driver, the default GLES driver on mainline kernels.
# The prebuilts are produced out of tree by mesa/build-mesa.sh. libinit sets
# ro.hardware.egl=mesa on mainline when they are installed; androidboot.cannon.egl=angle
# selects ANGLE instead, and the legacy 4.14 kernel keeps the Mali driver.
#
# LOCAL_PATH is this directory here: product makefiles are included with their
# own directory as LOCAL_PATH.

GFX_MESA_LIBS := libEGL_mesa.so libGLESv1_CM_mesa.so libGLESv2_mesa.so libgallium_dri.so

ifneq ($(wildcard $(LOCAL_PATH)/mesa/prebuilt/arm64/libEGL_mesa.so),)
PRODUCT_COPY_FILES += $(foreach lib,$(GFX_MESA_LIBS),\
    $(LOCAL_PATH)/mesa/prebuilt/arm64/$(lib):$(TARGET_COPY_OUT_VENDOR)/lib64/egl/$(lib))
endif

ifneq ($(wildcard $(LOCAL_PATH)/mesa/prebuilt/arm/libEGL_mesa.so),)
PRODUCT_COPY_FILES += $(foreach lib,$(GFX_MESA_LIBS),\
    $(LOCAL_PATH)/mesa/prebuilt/arm/$(lib):$(TARGET_COPY_OUT_VENDOR)/lib/egl/$(lib))
endif

# minigbm gralloc0 module for Mesa (u_gralloc CrOS API): buffer fourcc,
# modifier and plane layout, needed for YUV imports. The allocator and the
# stable-C mapper stay in the com.xiaomi.cannon.gralloc APEX; this is the same
# minigbm source, generic (dumb buffer) backend, so the handles match. Loaded
# only when libinit sets ro.hardware.gralloc=minigbm (mainline kernels).
PRODUCT_PACKAGES += \
    gralloc.minigbm
