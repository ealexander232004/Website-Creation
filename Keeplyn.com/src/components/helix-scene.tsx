"use client";

import { useEffect, useRef } from "react";
import * as THREE from "three";

const VIOLET = 0x7568ff;
const LIME = 0xc9ff3b;
const WHITE = 0xf7f7f4;

function createHelix(direction: 1 | -1, accent: number) {
  const group = new THREE.Group();
  const strandMaterial = new THREE.MeshBasicMaterial({
    color: accent,
    transparent: true,
    opacity: 0.44,
    blending: THREE.AdditiveBlending,
    depthWrite: false,
  });

  for (const phase of [0, Math.PI]) {
    const curvePoints: THREE.Vector3[] = [];
    for (let index = 0; index < 180; index += 1) {
      const angle = index * 0.19 * direction + phase;
      curvePoints.push(
        new THREE.Vector3(
          Math.cos(angle) * 1.18,
          (index - 90) * 0.073,
          Math.sin(angle) * 1.18,
        ),
      );
    }
    const curve = new THREE.CatmullRomCurve3(curvePoints);
    const tube = new THREE.Mesh(
      new THREE.TubeGeometry(curve, 360, 0.025, 6, false),
      strandMaterial,
    );
    group.add(tube);
  }

  const beadCount = 104;
  const beadGeometry = new THREE.IcosahedronGeometry(0.085, 1);
  const beadMaterial = new THREE.MeshStandardMaterial({
    color: WHITE,
    emissive: accent,
    emissiveIntensity: 0.58,
    metalness: 0.22,
    roughness: 0.28,
    vertexColors: true,
  });
  const beads = new THREE.InstancedMesh(beadGeometry, beadMaterial, beadCount * 2);
  const dummy = new THREE.Object3D();
  const white = new THREE.Color(WHITE);
  const violet = new THREE.Color(VIOLET);
  const lime = new THREE.Color(LIME);
  const rungs: number[] = [];

  for (let index = 0; index < beadCount; index += 1) {
    const angle = index * 0.325 * direction;
    const y = (index - beadCount / 2) * 0.126;
    const pulse = 1.16 + Math.sin(index * 0.33) * 0.045;
    const first = new THREE.Vector3(Math.cos(angle) * pulse, y, Math.sin(angle) * pulse);
    const second = new THREE.Vector3(
      Math.cos(angle + Math.PI) * pulse,
      y,
      Math.sin(angle + Math.PI) * pulse,
    );

    dummy.position.copy(first);
    dummy.scale.setScalar(index % 13 === 0 ? 1.7 : index % 5 === 0 ? 1.25 : 1);
    dummy.updateMatrix();
    beads.setMatrixAt(index * 2, dummy.matrix);
    beads.setColorAt(index * 2, index % 17 === 0 ? lime : white);

    dummy.position.copy(second);
    dummy.scale.setScalar(index % 11 === 0 ? 1.55 : 1);
    dummy.updateMatrix();
    beads.setMatrixAt(index * 2 + 1, dummy.matrix);
    beads.setColorAt(index * 2 + 1, index % 7 === 0 ? violet : white);

    if (index % 3 === 0) {
      rungs.push(first.x, first.y, first.z, second.x, second.y, second.z);
    }
  }
  beads.instanceMatrix.needsUpdate = true;
  if (beads.instanceColor) beads.instanceColor.needsUpdate = true;
  group.add(beads);

  const rungGeometry = new THREE.BufferGeometry();
  rungGeometry.setAttribute("position", new THREE.Float32BufferAttribute(rungs, 3));
  group.add(
    new THREE.LineSegments(
      rungGeometry,
      new THREE.LineBasicMaterial({
        color: accent,
        transparent: true,
        opacity: 0.34,
        blending: THREE.AdditiveBlending,
      }),
    ),
  );

  const orbitGroup = new THREE.Group();
  for (let index = 0; index < 4; index += 1) {
    const orbit = new THREE.Mesh(
      new THREE.TorusGeometry(1.7 + index * 0.22, 0.008, 5, 150),
      new THREE.MeshBasicMaterial({
        color: index === 3 ? LIME : accent,
        transparent: true,
        opacity: 0.13 + index * 0.025,
        blending: THREE.AdditiveBlending,
      }),
    );
    orbit.rotation.set(index * 0.52, index * 0.37, index * 0.7);
    orbitGroup.add(orbit);
  }

  const nodeGeometry = new THREE.IcosahedronGeometry(0.07, 1);
  const nodeMaterial = new THREE.MeshBasicMaterial({ color: LIME });
  for (let index = 0; index < 9; index += 1) {
    const node = new THREE.Mesh(nodeGeometry, nodeMaterial);
    const angle = (index / 9) * Math.PI * 2;
    node.position.set(Math.cos(angle) * 2.28, Math.sin(angle * 2) * 1.45, Math.sin(angle) * 2.28);
    orbitGroup.add(node);
  }
  group.add(orbitGroup);
  group.userData.orbits = orbitGroup;
  return group;
}

export function HelixScene() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const sceneCanvas = canvas;

    let renderer: THREE.WebGLRenderer;
    try {
      renderer = new THREE.WebGLRenderer({
        canvas: sceneCanvas,
        alpha: true,
        antialias: true,
        powerPreference: "high-performance",
      });
    } catch {
      return;
    }

    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.65));
    renderer.setClearColor(0x050505, 0);
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.25;

    const scene = new THREE.Scene();
    scene.fog = new THREE.FogExp2(0x050505, 0.042);
    const camera = new THREE.PerspectiveCamera(46, 1, 0.1, 80);
    camera.position.set(0, 0, 13.8);

    const leftHelix = createHelix(1, VIOLET);
    const rightHelix = createHelix(-1, 0x9f96ff);
    leftHelix.rotation.z = -0.14;
    rightHelix.rotation.z = 0.14;
    scene.add(leftHelix, rightHelix);

    const lattice = new THREE.LineSegments(
      new THREE.WireframeGeometry(new THREE.IcosahedronGeometry(2.55, 4)),
      new THREE.LineBasicMaterial({
        color: VIOLET,
        transparent: true,
        opacity: 0.065,
        blending: THREE.AdditiveBlending,
      }),
    );
    lattice.position.z = -2.6;
    scene.add(lattice);

    const knot = new THREE.Mesh(
      new THREE.TorusKnotGeometry(2.3, 0.017, 420, 10, 3, 7),
      new THREE.MeshBasicMaterial({
        color: LIME,
        transparent: true,
        opacity: 0.09,
        wireframe: true,
        blending: THREE.AdditiveBlending,
      }),
    );
    knot.position.z = -1.2;
    knot.rotation.set(0.55, 0.1, 0.4);
    scene.add(knot);

    const particleCount = window.innerWidth < 640 ? 650 : 1450;
    const particlePositions = new Float32Array(particleCount * 3);
    const particleColors = new Float32Array(particleCount * 3);
    const violet = new THREE.Color(VIOLET);
    const white = new THREE.Color(WHITE);
    const lime = new THREE.Color(LIME);
    for (let index = 0; index < particleCount; index += 1) {
      const radius = 4.5 + Math.random() * 12;
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos(2 * Math.random() - 1);
      particlePositions[index * 3] = radius * Math.sin(phi) * Math.cos(theta);
      particlePositions[index * 3 + 1] = radius * Math.sin(phi) * Math.sin(theta);
      particlePositions[index * 3 + 2] = radius * Math.cos(phi) - 3;
      const color = index % 41 === 0 ? lime : index % 6 === 0 ? white : violet;
      color.toArray(particleColors, index * 3);
    }
    const particleGeometry = new THREE.BufferGeometry();
    particleGeometry.setAttribute("position", new THREE.BufferAttribute(particlePositions, 3));
    particleGeometry.setAttribute("color", new THREE.BufferAttribute(particleColors, 3));
    const particles = new THREE.Points(
      particleGeometry,
      new THREE.PointsMaterial({
        size: 0.032,
        transparent: true,
        opacity: 0.68,
        vertexColors: true,
        depthWrite: false,
        blending: THREE.AdditiveBlending,
      }),
    );
    scene.add(particles);

    scene.add(new THREE.AmbientLight(WHITE, 1.65));
    const violetLight = new THREE.PointLight(VIOLET, 52, 28, 2);
    violetLight.position.set(0, 5, 8);
    scene.add(violetLight);
    const limeLight = new THREE.PointLight(LIME, 27, 24, 2);
    limeLight.position.set(-6, -4, 5);
    scene.add(limeLight);

    let targetScroll = 0;
    let scrollRotation = 0;
    let scrollVelocity = 0;
    let scrollOffset = 0;
    let previousScrollY = window.scrollY;
    let smoothScrollTarget = window.scrollY;
    let smoothScrollActive = false;
    let previousFrameTime = 0;
    let frame = 0;
    const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    sceneCanvas.dataset.motionMode = reducedMotion ? "helix-idle-and-gentle-scroll" : "idle-and-gentle-scroll";
    sceneCanvas.dataset.pointerMotion = "off";
    sceneCanvas.dataset.scrollScale = "0.333";

    const updateWheel = (event: WheelEvent) => {
      if (event.ctrlKey || Math.abs(event.deltaX) > Math.abs(event.deltaY)) return;
      event.preventDefault();
      const unit = event.deltaMode === WheelEvent.DOM_DELTA_LINE
        ? 16
        : event.deltaMode === WheelEvent.DOM_DELTA_PAGE
          ? window.innerHeight
          : 1;
      const scaledDelta = event.deltaY * unit / 3;
      const maxScroll = Math.max(document.documentElement.scrollHeight - window.innerHeight, 0);
      if (!smoothScrollActive) smoothScrollTarget = window.scrollY;
      smoothScrollTarget = THREE.MathUtils.clamp(smoothScrollTarget + scaledDelta, 0, maxScroll);
      smoothScrollActive = true;
      sceneCanvas.dataset.wheelDelta = scaledDelta.toFixed(3);
      sceneCanvas.dataset.scrollTarget = smoothScrollTarget.toFixed(3);
    };
    const updateScroll = () => {
      const currentScrollY = window.scrollY;
      const scrollDelta = currentScrollY - previousScrollY;
      scrollVelocity += THREE.MathUtils.clamp(scrollDelta * 0.00018, -0.055, 0.055);
      previousScrollY = currentScrollY;
      if (!smoothScrollActive) smoothScrollTarget = currentScrollY;
      const distance = Math.max(document.documentElement.scrollHeight - window.innerHeight, 1);
      targetScroll = currentScrollY / distance;
      sceneCanvas.dataset.scrollProgress = targetScroll.toFixed(3);
    };

    const resize = () => {
      const { clientWidth, clientHeight } = sceneCanvas;
      if (!clientWidth || !clientHeight) return;
      renderer.setSize(clientWidth, clientHeight, false);
      camera.aspect = clientWidth / clientHeight;
      camera.updateProjectionMatrix();
      const isMobile = clientWidth < 640;
      const horizontal = isMobile ? 1.68 : Math.min(5.15, Math.max(2.8, camera.aspect * 2.78));
      const scale = isMobile ? 0.74 : 1;
      camera.position.z = isMobile ? 12.4 : 13.8;
      leftHelix.position.x = -horizontal;
      rightHelix.position.x = horizontal;
      leftHelix.scale.setScalar(scale);
      rightHelix.scale.setScalar(scale);
    };

    const resizeObserver = new ResizeObserver(resize);
    resizeObserver.observe(sceneCanvas);
    window.addEventListener("wheel", updateWheel, { passive: false });
    window.addEventListener("scroll", updateScroll, { passive: true });
    updateScroll();
    resize();

    const render = (time = 0) => {
      const deltaSeconds = previousFrameTime
        ? Math.min((time - previousFrameTime) / 1000, 0.05)
        : 1 / 60;
      previousFrameTime = time;
      const helixElapsed = time * 0.001;
      const elapsed = reducedMotion ? 0 : helixElapsed;
      if (smoothScrollActive) {
        const scrollDistance = smoothScrollTarget - window.scrollY;
        const scrollEase = reducedMotion ? 1 : 1 - Math.pow(0.002, deltaSeconds);
        if (Math.abs(scrollDistance) < 0.35) {
          window.scrollTo(0, smoothScrollTarget);
          smoothScrollActive = false;
        } else {
          window.scrollTo(0, window.scrollY + scrollDistance * scrollEase);
        }
      }
      const rotationFollow = 1 - Math.pow(0.01, deltaSeconds);
      scrollRotation += (targetScroll - scrollRotation) * rotationFollow;
      scrollVelocity *= Math.pow(0.006, deltaSeconds);
      scrollOffset += scrollVelocity * Math.min(deltaSeconds * 60, 2);
      const idleSpin = helixElapsed * 0.17;
      const scrollSpin = scrollRotation * Math.PI * 2.4 + scrollOffset;
      const combinedSpin = idleSpin + scrollSpin;

      leftHelix.rotation.y = combinedSpin;
      rightHelix.rotation.y = -combinedSpin * 0.94;
      leftHelix.rotation.x = -0.12 + scrollRotation * 0.16;
      rightHelix.rotation.x = 0.12 - scrollRotation * 0.16;
      leftHelix.position.y = -scrollRotation * 0.23;
      rightHelix.position.y = scrollRotation * 0.23;

      const leftOrbits = leftHelix.userData.orbits as THREE.Group;
      const rightOrbits = rightHelix.userData.orbits as THREE.Group;
      leftOrbits.rotation.z = elapsed * 0.22 + scrollSpin * 0.45;
      leftOrbits.rotation.x = elapsed * 0.12;
      rightOrbits.rotation.z = elapsed * -0.19 - scrollSpin * 0.45;
      rightOrbits.rotation.x = elapsed * -0.1;

      lattice.rotation.y = elapsed * 0.035 + scrollSpin * 0.15;
      lattice.rotation.x = elapsed * -0.025 + scrollRotation * 0.4;
      knot.rotation.y = elapsed * -0.075 - scrollSpin * 0.09;
      knot.rotation.z = elapsed * 0.05 + scrollRotation * 0.6;
      particles.rotation.y = elapsed * 0.008 + scrollSpin * 0.025;
      particles.rotation.x = elapsed * -0.005;
      camera.lookAt(0, 0, 0);
      renderer.render(scene, camera);
      sceneCanvas.dataset.spin = combinedSpin.toFixed(3);
      sceneCanvas.dataset.scrollVelocity = scrollVelocity.toFixed(3);
      frame = window.requestAnimationFrame(render);
    };
    render();

    return () => {
      window.cancelAnimationFrame(frame);
      window.removeEventListener("wheel", updateWheel);
      window.removeEventListener("scroll", updateScroll);
      resizeObserver.disconnect();
      const geometries = new Set<THREE.BufferGeometry>();
      const materials = new Set<THREE.Material>();
      scene.traverse((object) => {
        if (object instanceof THREE.Mesh || object instanceof THREE.LineSegments || object instanceof THREE.Points) {
          geometries.add(object.geometry);
          const objectMaterials = Array.isArray(object.material) ? object.material : [object.material];
          objectMaterials.forEach((material) => materials.add(material));
        }
      });
      geometries.forEach((geometry) => geometry.dispose());
      materials.forEach((material) => material.dispose());
      renderer.dispose();
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      className="size-full"
      data-scroll-progress="0.000"
      aria-hidden="true"
    />
  );
}
