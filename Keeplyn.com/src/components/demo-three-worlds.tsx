"use client";

import { useEffect, useRef } from "react";
import * as THREE from "three";

export type DemoWorldVariant = "moss" | "northline" | "sera";

type DemoWorld3DProps = {
  variant: DemoWorldVariant;
  className?: string;
};

type WorldScene = {
  root: THREE.Group;
  update: (time: number, delta: number) => void;
};

const TAU = Math.PI * 2;

function seeded(index: number, salt = 0) {
  const value = Math.sin(index * 127.1 + salt * 311.7) * 43758.5453;
  return value - Math.floor(value);
}

function addPollen(
  scene: THREE.Scene,
  color: number,
  count: number,
  spread: readonly [number, number, number],
  size: number,
  salt: number,
) {
  const positions = new Float32Array(count * 3);
  for (let index = 0; index < count; index += 1) {
    positions[index * 3] = (seeded(index, salt) - 0.5) * spread[0];
    positions[index * 3 + 1] = (seeded(index, salt + 1) - 0.5) * spread[1];
    positions[index * 3 + 2] = (seeded(index, salt + 2) - 0.5) * spread[2];
  }
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute("position", new THREE.BufferAttribute(positions, 3));
  const particles = new THREE.Points(
    geometry,
    new THREE.PointsMaterial({
      color,
      size,
      transparent: true,
      opacity: 0.58,
      depthWrite: false,
    }),
  );
  scene.add(particles);
  return particles;
}

function addShadowFloor(scene: THREE.Scene, color: number) {
  const floor = new THREE.Mesh(
    new THREE.CircleGeometry(4.2, 80),
    new THREE.ShadowMaterial({ color, opacity: 0.2, transparent: true }),
  );
  floor.rotation.x = -Math.PI / 2;
  floor.position.y = -2.2;
  floor.receiveShadow = true;
  scene.add(floor);
}

function buildMossWorld(scene: THREE.Scene): WorldScene {
  const root = new THREE.Group();
  root.rotation.set(-0.14, -0.38, -0.03);
  scene.add(root);

  const terrain = new THREE.Mesh(
    new THREE.IcosahedronGeometry(1.45, 4),
    new THREE.MeshPhysicalMaterial({
      color: 0x284c32,
      roughness: 0.62,
      metalness: 0.02,
      clearcoat: 0.28,
      clearcoatRoughness: 0.48,
    }),
  );
  terrain.scale.set(1.25, 0.76, 1);
  terrain.rotation.set(0.2, 0.15, -0.08);
  terrain.castShadow = true;
  terrain.receiveShadow = true;
  root.add(terrain);

  const contour = new THREE.Mesh(
    new THREE.IcosahedronGeometry(1.62, 2),
    new THREE.MeshBasicMaterial({
      color: 0xc9ff3b,
      wireframe: true,
      transparent: true,
      opacity: 0.16,
    }),
  );
  contour.scale.copy(terrain.scale).multiplyScalar(1.02);
  root.add(contour);

  const vineMaterial = new THREE.MeshStandardMaterial({ color: 0x83a979, roughness: 0.45 });
  const limeMaterial = new THREE.MeshStandardMaterial({
    color: 0xc9ff3b,
    emissive: 0x6c9416,
    emissiveIntensity: 0.5,
    roughness: 0.34,
  });
  const leafGeometry = new THREE.SphereGeometry(0.16, 18, 12);
  const vines = new THREE.Group();

  for (let vineIndex = 0; vineIndex < 5; vineIndex += 1) {
    const points: THREE.Vector3[] = [];
    for (let pointIndex = 0; pointIndex < 10; pointIndex += 1) {
      const progress = pointIndex / 9;
      const angle = progress * TAU * (1.05 + vineIndex * 0.08) + vineIndex * 1.17;
      const radius = 1.62 + Math.sin(progress * Math.PI * 3 + vineIndex) * 0.16;
      points.push(new THREE.Vector3(
        Math.cos(angle) * radius,
        (progress - 0.5) * 4.25 + Math.sin(angle * 0.7) * 0.2,
        Math.sin(angle) * radius * 0.72,
      ));
    }
    const curve = new THREE.CatmullRomCurve3(points);
    const vine = new THREE.Mesh(
      new THREE.TubeGeometry(curve, 120, vineIndex % 2 === 0 ? 0.045 : 0.03, 10, false),
      vineIndex === 2 ? limeMaterial : vineMaterial,
    );
    vine.castShadow = true;
    vines.add(vine);

    for (let leafIndex = 1; leafIndex < 9; leafIndex += 1) {
      const progress = (leafIndex + 0.25 + vineIndex * 0.17) / 9.5;
      const leaf = new THREE.Mesh(leafGeometry, (leafIndex + vineIndex) % 5 === 0 ? limeMaterial : vineMaterial);
      leaf.position.copy(curve.getPoint(Math.min(progress, 0.96)));
      const tangent = curve.getTangent(Math.min(progress, 0.96)).normalize();
      leaf.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), tangent);
      leaf.rotateZ((leafIndex % 2 === 0 ? 1 : -1) * 0.92);
      leaf.scale.set(1.3 + seeded(leafIndex, vineIndex) * 0.45, 0.42, 0.16);
      leaf.castShadow = true;
      vines.add(leaf);
    }
  }
  root.add(vines);

  const stoneGeometry = new THREE.DodecahedronGeometry(0.34, 1);
  const stoneMaterial = new THREE.MeshStandardMaterial({ color: 0xaebba1, roughness: 0.86 });
  const stones = new THREE.Group();
  for (let index = 0; index < 8; index += 1) {
    const stone = new THREE.Mesh(stoneGeometry, stoneMaterial);
    const angle = (index / 8) * TAU;
    stone.position.set(Math.cos(angle) * (2.25 + seeded(index, 9) * 0.4), -1.45 + seeded(index, 10) * 0.5, Math.sin(angle) * 1.42);
    stone.scale.setScalar(0.55 + seeded(index, 11) * 0.95);
    stone.rotation.set(seeded(index, 12) * 2, seeded(index, 13) * 2, seeded(index, 14) * 2);
    stone.castShadow = true;
    stones.add(stone);
  }
  root.add(stones);

  const pollen = addPollen(scene, 0xc9ff3b, 240, [8.5, 6.5, 6], 0.028, 21);
  addShadowFloor(scene, 0x07130b);

  return {
    root,
    update: (time, delta) => {
      root.rotation.y += delta * 0.075;
      vines.rotation.y -= delta * 0.035;
      contour.rotation.y += delta * 0.12;
      terrain.rotation.z = -0.08 + Math.sin(time * 0.00035) * 0.045;
      pollen.rotation.y = time * 0.000018;
    },
  };
}

function buildNorthlineWorld(scene: THREE.Scene): WorldScene {
  const root = new THREE.Group();
  root.rotation.set(-0.16, -0.2, 0.04);
  scene.add(root);

  const glassMaterial = new THREE.MeshPhysicalMaterial({
    color: 0xbfe7f5,
    metalness: 0.04,
    roughness: 0.08,
    transmission: 0.82,
    transparent: true,
    opacity: 0.94,
    thickness: 1.65,
    clearcoat: 1,
    clearcoatRoughness: 0.04,
  });
  const loop = new THREE.Mesh(new THREE.TorusKnotGeometry(1.22, 0.34, 220, 32, 2, 3), glassMaterial);
  loop.scale.set(1, 1.05, 0.9);
  loop.castShadow = true;
  root.add(loop);

  const coralMaterial = new THREE.MeshStandardMaterial({
    color: 0xff725e,
    emissive: 0xc5372c,
    emissiveIntensity: 0.72,
    roughness: 0.32,
  });
  const core = new THREE.Mesh(new THREE.OctahedronGeometry(0.7, 3), coralMaterial);
  core.castShadow = true;
  root.add(core);

  const haloMaterial = new THREE.MeshPhysicalMaterial({
    color: 0xffffff,
    emissive: 0x8bcce7,
    emissiveIntensity: 0.36,
    metalness: 0.55,
    roughness: 0.18,
    transparent: true,
    opacity: 0.88,
  });
  const halos = [
    [1.95, 0.04, 1.05, 0.18, 0.36],
    [2.4, 0.026, 0.24, 1.12, -0.44],
    [2.78, 0.018, 1.38, -0.36, 0.68],
  ].map(([radius, tube, x, y, z]) => {
    const halo = new THREE.Mesh(new THREE.TorusGeometry(radius, tube, 14, 180), haloMaterial);
    halo.rotation.set(x, y, z);
    root.add(halo);
    return halo;
  });

  const smileCurve = new THREE.QuadraticBezierCurve3(
    new THREE.Vector3(-1.45, -0.2, 0.94),
    new THREE.Vector3(0, -1.38, 1.18),
    new THREE.Vector3(1.45, -0.2, 0.94),
  );
  const smile = new THREE.Mesh(new THREE.TubeGeometry(smileCurve, 72, 0.075, 14, false), coralMaterial);
  smile.castShadow = true;
  root.add(smile);

  const satelliteGeometry = new THREE.SphereGeometry(0.09, 20, 20);
  const satelliteMaterial = new THREE.MeshStandardMaterial({ color: 0xffffff, emissive: 0x9ed9ef, emissiveIntensity: 0.7, roughness: 0.2 });
  const satellites = new THREE.Group();
  for (let index = 0; index < 14; index += 1) {
    const satellite = new THREE.Mesh(satelliteGeometry, index % 5 === 0 ? coralMaterial : satelliteMaterial);
    const angle = (index / 14) * TAU;
    const radius = index % 2 === 0 ? 2.15 : 2.72;
    satellite.position.set(Math.cos(angle) * radius, Math.sin(angle * 1.7) * 1.36, Math.sin(angle) * radius * 0.48);
    satellite.scale.setScalar(index % 4 === 0 ? 1.55 : 1);
    satellite.castShadow = true;
    satellites.add(satellite);
  }
  root.add(satellites);

  const signal = addPollen(scene, 0x173a5a, 280, [8, 6, 6], 0.023, 31);
  addShadowFloor(scene, 0x173a5a);

  return {
    root,
    update: (time, delta) => {
      root.rotation.y += delta * 0.13;
      loop.rotation.z += delta * 0.1;
      satellites.rotation.z -= delta * 0.1;
      halos[0].rotation.z += delta * 0.1;
      halos[1].rotation.x -= delta * 0.075;
      halos[2].rotation.y += delta * 0.055;
      core.scale.setScalar(1 + Math.sin(time * 0.00145) * 0.055);
      signal.rotation.y = time * 0.000014;
    },
  };
}

function buildSeraWorld(scene: THREE.Scene): WorldScene {
  const root = new THREE.Group();
  root.rotation.set(-0.22, -0.38, -0.05);
  scene.add(root);

  const doughMaterial = new THREE.MeshPhysicalMaterial({
    color: 0xe09a61,
    roughness: 0.58,
    metalness: 0.01,
    clearcoat: 0.34,
    clearcoatRoughness: 0.42,
  });
  const warmDoughMaterial = new THREE.MeshPhysicalMaterial({
    color: 0xf3c487,
    roughness: 0.66,
    clearcoat: 0.22,
    clearcoatRoughness: 0.5,
  });
  const doughGeometry = new THREE.SphereGeometry(0.9, 52, 36);
  const dough = new THREE.Group();
  const lobes: THREE.Mesh[] = [];

  const center = new THREE.Mesh(doughGeometry, warmDoughMaterial);
  center.scale.set(1.22, 1, 1.1);
  center.castShadow = true;
  dough.add(center);
  lobes.push(center);

  for (let index = 0; index < 6; index += 1) {
    const angle = (index / 6) * TAU;
    const lobe = new THREE.Mesh(doughGeometry, index % 2 === 0 ? doughMaterial : warmDoughMaterial);
    lobe.position.set(Math.cos(angle) * 1.03, Math.sin(angle) * 0.86, Math.sin(angle * 1.5) * 0.34);
    lobe.scale.set(1.04, 0.9, 0.92);
    lobe.rotation.set(angle * 0.15, angle, -angle * 0.08);
    lobe.castShadow = true;
    lobe.receiveShadow = true;
    dough.add(lobe);
    lobes.push(lobe);
  }
  dough.scale.set(1.03, 1.03, 1.03);
  root.add(dough);

  const scoreMaterial = new THREE.MeshStandardMaterial({
    color: 0xfff2dc,
    emissive: 0xd98454,
    emissiveIntensity: 0.3,
    roughness: 0.48,
  });
  const scores = new THREE.Group();
  [-0.58, 0, 0.58].forEach((offset, index) => {
    const curve = new THREE.QuadraticBezierCurve3(
      new THREE.Vector3(-1.25, 0.45 + offset * 0.42, 1.04),
      new THREE.Vector3(0, 0.9 + offset * 0.32, 1.38 + index * 0.02),
      new THREE.Vector3(1.25, 0.45 + offset * 0.42, 1.04),
    );
    const score = new THREE.Mesh(new THREE.TubeGeometry(curve, 60, 0.055, 12, false), scoreMaterial);
    score.castShadow = true;
    scores.add(score);
  });
  root.add(scores);

  const goldMaterial = new THREE.MeshStandardMaterial({
    color: 0xf4c96f,
    emissive: 0xa95432,
    emissiveIntensity: 0.32,
    roughness: 0.32,
    transparent: true,
    opacity: 0.88,
  });
  const orbit = new THREE.Mesh(new THREE.TorusKnotGeometry(2.03, 0.032, 200, 12, 3, 2), goldMaterial);
  orbit.rotation.set(0.82, 0.3, 0.22);
  root.add(orbit);

  const bubbleGeometry = new THREE.SphereGeometry(0.08, 16, 16);
  const bubbles = new THREE.Group();
  for (let index = 0; index < 24; index += 1) {
    const bubble = new THREE.Mesh(bubbleGeometry, index % 4 === 0 ? scoreMaterial : goldMaterial);
    const angle = (index / 24) * TAU;
    const radius = 2.15 + seeded(index, 45) * 0.82;
    bubble.position.set(Math.cos(angle) * radius, (seeded(index, 46) - 0.5) * 4.25, Math.sin(angle) * radius * 0.55);
    bubble.scale.setScalar(0.7 + seeded(index, 47) * 1.4);
    bubbles.add(bubble);
  }
  root.add(bubbles);

  const flour = addPollen(scene, 0xfff2dc, 300, [8.5, 6.4, 6], 0.028, 41);
  addShadowFloor(scene, 0x4f211b);

  return {
    root,
    update: (time, delta) => {
      root.rotation.y += delta * 0.085;
      dough.rotation.z = Math.sin(time * 0.00028) * 0.055;
      orbit.rotation.z += delta * 0.11;
      bubbles.rotation.y -= delta * 0.07;
      lobes.forEach((lobe, index) => {
        const breath = 1 + Math.sin(time * 0.0012 + index * 0.82) * 0.025;
        lobe.scale.multiplyScalar(breath / (lobe.userData.previousBreath ?? 1));
        lobe.userData.previousBreath = breath;
      });
      flour.rotation.y = -time * 0.000016;
    },
  };
}

const worldBuilders: Record<DemoWorldVariant, (scene: THREE.Scene) => WorldScene> = {
  moss: buildMossWorld,
  northline: buildNorthlineWorld,
  sera: buildSeraWorld,
};

const worldLighting: Record<DemoWorldVariant, {
  ambient: number;
  key: number;
  fill: number;
  background: number;
}> = {
  moss: { ambient: 0xdce9d3, key: 0xc9ff3b, fill: 0x7b9f76, background: 0x112118 },
  northline: { ambient: 0xffffff, key: 0xff725e, fill: 0xa7def1, background: 0xd9eff8 },
  sera: { ambient: 0xffecd3, key: 0xff765f, fill: 0xf4c96f, background: 0x5d2d26 },
};

export function DemoWorld3D({ variant, className = "" }: DemoWorld3DProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    let renderer: THREE.WebGLRenderer;
    try {
      renderer = new THREE.WebGLRenderer({
        canvas,
        alpha: true,
        antialias: true,
        powerPreference: "high-performance",
      });
    } catch {
      return;
    }

    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.65));
    renderer.setClearColor(0x000000, 0);
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = variant === "moss" ? 1.16 : 1.22;
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFShadowMap;

    const scene = new THREE.Scene();
    const lighting = worldLighting[variant];
    scene.fog = new THREE.Fog(lighting.background, 7, 13);

    const camera = new THREE.PerspectiveCamera(38, 1, 0.1, 30);
    camera.position.set(0, 0.15, 7.6);

    const world = worldBuilders[variant](scene);
    scene.add(new THREE.HemisphereLight(lighting.ambient, lighting.background, 2.2));

    const keyLight = new THREE.DirectionalLight(lighting.key, 4.8);
    keyLight.position.set(-3.8, 5.4, 5.8);
    keyLight.castShadow = true;
    keyLight.shadow.mapSize.set(1024, 1024);
    keyLight.shadow.camera.near = 0.1;
    keyLight.shadow.camera.far = 18;
    scene.add(keyLight);

    const fillLight = new THREE.PointLight(lighting.fill, 42, 18, 2);
    fillLight.position.set(4.2, -1.8, 4.6);
    scene.add(fillLight);

    const pointer = new THREE.Vector2();
    const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    let frame = 0;
    let previousTime = 0;
    let running = true;

    const renderFrame = (time = 0) => {
      const delta = Math.min((time - previousTime) / 1000 || 0, 0.05);
      previousTime = time;
      world.update(time, delta);
      world.root.rotation.x += ((-0.14 - pointer.y * 0.13) - world.root.rotation.x) * 0.035;
      world.root.rotation.z += ((pointer.x * 0.07) - world.root.rotation.z) * 0.035;
      camera.position.x += ((pointer.x * 0.24) - camera.position.x) * 0.025;
      camera.position.y += ((0.15 - pointer.y * 0.18) - camera.position.y) * 0.025;
      camera.lookAt(0, 0, 0);
      renderer.render(scene, camera);
      canvas.dataset.rendered = "true";
      canvas.dataset.sceneObjects = String(scene.children.length);
      if (running && !reducedMotion) frame = window.requestAnimationFrame(renderFrame);
    };

    const resize = () => {
      const width = canvas.clientWidth;
      const height = canvas.clientHeight;
      if (!width || !height) return;
      renderer.setSize(width, height, false);
      camera.aspect = width / height;
      camera.position.z = width < 520 ? 8.6 : 7.6;
      camera.updateProjectionMatrix();
      if (reducedMotion) renderFrame();
    };

    const handlePointerMove = (event: PointerEvent) => {
      const bounds = canvas.getBoundingClientRect();
      pointer.x = ((event.clientX - bounds.left) / Math.max(bounds.width, 1) - 0.5) * 2;
      pointer.y = ((event.clientY - bounds.top) / Math.max(bounds.height, 1) - 0.5) * 2;
      if (reducedMotion) {
        world.root.rotation.x = -0.14 - pointer.y * 0.1;
        world.root.rotation.z = pointer.x * 0.06;
        renderer.render(scene, camera);
      }
    };

    const handlePointerLeave = () => pointer.set(0, 0);
    const resizeObserver = new ResizeObserver(resize);
    resizeObserver.observe(canvas);
    canvas.addEventListener("pointermove", handlePointerMove, { passive: true });
    canvas.addEventListener("pointerleave", handlePointerLeave);

    const intersectionObserver = new IntersectionObserver(([entry]) => {
      const shouldRun = entry?.isIntersecting ?? true;
      if (shouldRun === running || reducedMotion) return;
      running = shouldRun;
      if (running) {
        previousTime = performance.now();
        frame = window.requestAnimationFrame(renderFrame);
      } else {
        window.cancelAnimationFrame(frame);
      }
    }, { rootMargin: "180px" });
    intersectionObserver.observe(canvas);

    resize();
    renderFrame();

    return () => {
      running = false;
      window.cancelAnimationFrame(frame);
      resizeObserver.disconnect();
      intersectionObserver.disconnect();
      canvas.removeEventListener("pointermove", handlePointerMove);
      canvas.removeEventListener("pointerleave", handlePointerLeave);

      const geometries = new Set<THREE.BufferGeometry>();
      const materials = new Set<THREE.Material>();
      scene.traverse((object) => {
        if (object instanceof THREE.Mesh || object instanceof THREE.Points || object instanceof THREE.Line) {
          geometries.add(object.geometry);
          const objectMaterials = Array.isArray(object.material) ? object.material : [object.material];
          objectMaterials.forEach((material) => materials.add(material));
        }
      });
      geometries.forEach((geometry) => geometry.dispose());
      materials.forEach((material) => material.dispose());
      renderer.dispose();
      renderer.forceContextLoss();
    };
  }, [variant]);

  return (
    <canvas
      ref={canvasRef}
      className={`demo-world-canvas ${className}`}
      data-visual={`three-dimensional-${variant}-world`}
      aria-hidden="true"
    />
  );
}
