# SO-101 Bimanual Genesis Simulation — Final Tasarım Raporu

Bu noktada V1 için gerekli ana kararlar kilitlenebilir. Hedef; kontrolcünün Genesis'i bilmesine gerek kalmadan ROS 2 üzerinden iki gerçek SO-101 follower kol kullanıyormuş gibi çalışabildiği, buna karşılık geliştiricinin aynı anda simülasyonun kusursuz ground-truth durumuna erişebildiği taşınabilir bir test ortamı.

---

# I. Genel Tasarım Kararları

## 1. Yapmak istediğimiz sistem

Tek bir Genesis fizik dünyasında:

* 2 × SO-101 follower robot,
* aynı masa üzerinde yan yana,
* ortak çalışma hacmine sahip,
* birbirleriyle ve aynı objeyle fiziksel temas kurabilen,
* basit kutu/silindir/küre objelerini birlikte manipüle edebilen,
* kamera/perception içermeyen,
* kontrol algoritması içermeyen,
* tamamen ROS 2 üzerinden dışarı açılan

bir simülasyon kurulacak.

Kontrolcü simülasyonun dışında olacak.

Ana sınır:

```text
                  ROS 2
                    │
          ┌─────────┴─────────┐
          │                   │
     Controller          Debug / tools
          │                   │
          ▼                   ▼
   joint targets       ground truth state
          │
          ▼
 ┌───────────────────────────────┐
 │       SO-101 Simulation       │
 │                               │
 │  command interface            │
 │       ↓                       │
 │  servo/gearbox model          │
 │       ↓                       │
 │  Genesis physics              │
 │       ↓                       │
 │  encoder model                │
 └───────┬──────────────┬────────┘
         │              │
         ▼              ▼
 measured state    ground truth state
```

Kontrolcü normal kullanımda yalnızca measured/noisy state'i kullanacak. Ground truth özellikle debugging, karşılaştırma, controller tuning ve simülasyon doğrulaması için ayrıca yayınlanacak.

---

## 2. Referans gerçek robot

Referans robot:

**SO-101 follower + 6 × Feetech STS3215 7.4 V, 1:345**

olarak kilitleniyor.

LeRobot'un güncel SO-101 dokümantasyonu follower kolun altı STS3215 ve tüm follower motorlarının 1:345 redüksiyon kullandığını doğruluyor. ([GitHub][1])

STS3215'in 7.4 V varyantı için üretici/satıcı verileri:

* 12-bit magnetic absolute encoder
* 4096 count / revolution
* `360 / 4096 = 0.08789°/count`
* yaklaşık 19.5 kg·cm stall torque @ 7.4 V
* yaklaşık 0.192 s / 60° no-load speed @ 7.4 V
* position, speed, load, voltage vb. geri bildirim

veriyor. ([Waveshare][2])

Dolayısıyla V1 servo referansımız yaklaşık:

```text
Encoder resolution : 0.08789 deg/count
Stall torque       : 1.91 N·m
No-load speed      : 312.5 deg/s
                   : 5.45 rad/s
```

olacak.

Servo varyantı config içinde tutulacağı için daha sonra 12 V modeline geçmek mimari değişiklik gerektirmeyecek.

---

## 3. Gerçekçilik yaklaşımı

Burada amaç fotogerçekçilik değil, **control-relevant realism**.

Öncelik sırası:

1. doğru kinematik,
2. doğru joint limitleri,
3. doğru kütle ve inertia,
4. gerçekçi contact/collision,
5. gerçekçi servo dinamiği,
6. torque/speed saturation,
7. friction/damping,
8. gearbox backlash,
9. encoder quantization,
10. sensor/communication latency ve küçük ölçüm gürültüsü,
11. görsel gerçekçilik.

Orijinal CAD/STL kullanacağımız için robot zaten görsel olarak gerçek SO-101 olacaktır. Fizik davranışı ise controller geliştirme açısından görüntüden daha önemli kabul edilecek.

---

## 4. Kontrol prensibi

ROS'tan gelen hedef fizik state'ine doğrudan yazılmayacak.

Yani şu **yasak**:

```text
ROS target
   ↓
set joint position
   ↓
robot hedefe teleport
```

Genesis'in kendi dokümantasyonu da `set_*` fonksiyonlarını doğrudan state manipulation, `control_*` fonksiyonlarını ise fizik üzerinden actuated control olarak ayırıyor. `control_dofs_position()` PD kuvvetleri üreterek dynamics ve force limitlerini koruyor. ([Genesis World][3])

Bizim akışımız:

```text
ROS q_target
      ↓
target quantization
      ↓
servo/gearbox model
      ↓
position controller
      ↓
torque + speed limitations
      ↓
Genesis dynamics
      ↓
actual physical q
      ├─────────────→ ground truth
      │
      ↓
encoder model
      ↓
measured q
      ↓
ROS
```

olacak.

Bu, projenin en temel tasarım kararıdır.

---

## 5. ROS tasarım prensibi

V1 için `ros2_control` zorunlu değil.

Arkadaşının controller'ı için gereken ana sistem gerçekten söylediğin kadar basit:

```text
joint positions
       ↓
 controller
       ↓
desired joint positions
```

Bu nedenle ROS public interface basit tutulacak.

Ancak ROS adapter ile simulation core birbirinden ayrılacak. Böylece ileride:

* ros2_control,
* MoveIt 2,
* FollowJointTrajectory,
* farklı controller framework'leri

eklemek mümkün olacak.

Güncel `genesis_ros` projesi Ubuntu 24.04/Jazzy, `/clock`, `/tf`, `/joint_states`, `FollowJointTrajectory` ve ros2_control desteği sunuyor; ancak proje kendisini hâlâ genç bir bridge olarak tanımlıyor. Bizim kullanımımız çok daha küçük olduğu için runtime mimarimizi bu projeye bağımlı yapmayacağız. ([GitHub][4])

**Kendi ince ROS 2 adapter'ımızı yazacağız.**

Genesis ile `rclpy` aynı Python process içinde çalışacak.

---

## 6. Taşınabilirlik

Bu da artık ana tasarım şartlarından biri:

> Repository başka bilgisayara taşındığında elle ROS/Genesis/Python dependency kurulumu yapılmayacak.

Resmî çalışma şekli:

```bash
git clone ...
cd so101_bimanual_sim
./run.sh
```

olacak.

Host tarafında yalnızca:

* Docker Engine
* Docker Compose

gerekecek.

Container içinde:

```text
Ubuntu 24.04
ROS 2 Jazzy
Python 3.12
uv
Genesis
our ROS workspace
our simulation
```

bulunacak.

ROS 2 Jazzy, Ubuntu 24.04 Noble'ı destekliyor. Güncel Genesis ise Python 3.10–3.13 aralığını destekliyor ve CPU backend'i resmi olarak mevcut; dolayısıyla Python 3.12 bu iki dünya için doğal ortak seçim. ([ROS Documentation][5])

Python bağımlılıklarını:

```text
pyproject.toml
uv.lock
```

kilitleyecek.

ROS/system bağımlılıklarını Dockerfile kilitleyecek.

CPU default olacak; NVIDIA GPU varsa ayrı Docker profile ile kullanılabilecek.

---

# II. Detay Tasarım Kararları

# 1. Robot geometry ve asset modeli

Kaynak olarak resmi TheRobotStudio SO-101 simulation asset'leri kullanılacak.

Mevcut model:

* CAD tabanlı STL'ler,
* URDF,
* MJCF,
* link mass değerleri,
* inertia tensor'ları,
* gerçek joint origin'leri,
* gerçek joint limitleri

içeriyor. Model CAD'den `onshape-to-robot` kullanılarak oluşturulmuş. ([GitHub][6])

Visual model değiştirilmeden korunacak.

```text
Visual geometry
      =
official SO-101 STL
```

Physics collision geometry ise ayrı ele alınacak.

Genesis rigid URDF import ederken mesh decimation, convexification ve CoACD decomposition destekliyor. Robot collision'ları için bu mekanizmaları kullanabiliriz. ([Genesis World][7])

Özellikle:

```text
base / upper arm / lower arm
    → simple convex collision

wrist
    → simplified convex collision

gripper fingers
    → daha hassas collision geometry
```

kullanılacak.

Gripper collision modeline ekstra önem verilecek; çünkü bimanual object manipulation'ın doğruluğunu büyük ölçüde finger-object contact belirleyecek.

---

# 2. Gerçek URDF'ten çıkan robot erişimi

SO-101'in gerçek joint origin ve limitlerini kullanarak FK taraması yaptım.

URDF'teki ana link mesafeleri arasında yaklaşık:

```text
elbow → wrist       = 134.9 mm
wrist → gripper     ≈ 63.7 mm
gripper → TCP       ≈ 98.4 mm
```

gibi mesafeler bulunuyor; shoulder/elbow/wrist joint origin'leri ve limitleri de doğrudan kaynak URDF'te tanımlı. 

Yeni calibration modelinde tüm ilk beş arm joint'i `0 rad` iken FK sonucu gripper frame yaklaşık:

```text
x = 0.391 m ileri
y ≈ 0
z = 0.226 m yukarı
```

çıkıyor.

Tüm geçerli joint limitleri üzerinde yaptığım random FK taramasında maksimum yatay gripper-frame uzaklığı:

**≈ 0.479 m**

çıktı.

Bu sayı masa geometrisinin ana girdisi olacak.

---

# 3. İki robot arasındaki mesafe

İki robot:

* aynı yöne bakacak,
* aynı base orientation'a sahip olacak,
* yan yana yerleştirilecek.

Base center separation:

# **400 mm**

olarak kilitleniyor.

Yani:

```text
           shared workspace

                 ↑ +X

      LEFT                  RIGHT

       ●---------------------●
              400 mm
```

Bu değeri seçmenin nedeni yalnızca robotların birbirine sığması değil.

URDF joint limitlerinin %80'i içerisinde ve gripper'ın masa üzerinde yaklaşık `4–25 cm` yüksekliklerde bulunduğu daha konservatif FK taramasında, 400 mm base separation için iki robotun ortak kinematik çalışma alanının XY izdüşümü yaklaşık:

**0.118 m²**

çıkıyor.

Yaklaşık ortak bounding region:

```text
forward from base line:
~4 cm → 45 cm

centerline lateral:
~ -24 cm → +24 cm
```

Bu yalnızca kinematik overlap'tir; inter-arm collision filtering dahil değildir. Bu nedenle objeleri tüm overlap'a değil, daha içteki bir “core bimanual zone” içine koyacağız.

400 mm; 350 mm'ye göre biraz workspace kaybettiriyor ama iki kolun shoulder/base bölgelerinde gereksiz collision riskini azaltıyor.

---

# 4. Masa ölçüsü

Burada artık rastgele masa ölçüsü seçmiyoruz.

Bir robotun maksimum sampled lateral erişimi yaklaşık:

```text
± 0.439 m
```

İki base:

```text
±0.200 m
```

konumunda bulunursa tüm erişimi içeren yaklaşık lateral sınır:

```text
0.439 + 0.200 = 0.639 m
```

oluyor.

Dolayısıyla masa genişliği:

```text
2 × 0.639 = 1.278 m
```

çıkar.

Yuvarlayarak:

# **Masa genişliği = 1.30 m**

kilitleniyor.

Depth için robot base'ini arka kenardan 120 mm içeri koyuyoruz.

Maximum forward reach:

```text
120 mm + 479 mm = 599 mm
```

Buna yaklaşık 150 mm front safety margin eklersek:

```text
599 + 150 ≈ 749 mm
```

Dolayısıyla:

# **Masa derinliği = 0.75 m**

kilitleniyor.

Tam masa:

```text
Width     : 1.30 m
Depth     : 0.75 m
Thickness : 0.04 m
Height    : 0.75 m
```

İlk iki sayı robot kinematiğinden geliyor.

Thickness ve gerçek hayattaki 75 cm masa yüksekliği scene realism için seçilmiş pratik değerler; robot kontrol geometrisini değiştirmiyor.

---

# 5. Kesin scene coordinate sistemi

Simülasyonda world origin'i masanın üst yüzeyinin merkezine koyacağız:

```text
                         +X
                         ↑
                         │
       rear              │            front
  ─────────────────────────────────────────
                         │
              L ●        │       ● R
                         │
             -20cm       │      +20cm
                         │
─────────────────────────┼─────────────────── +Y
                         │
```

Tanım:

```text
+X : masanın önüne doğru
+Y : masanın soluna doğru
+Z : yukarı

table surface z = 0
```

Masa:

```text
X = [-0.375, +0.375]
Y = [-0.650, +0.650]
```

Base line arka kenardan 120 mm önde:

```text
base_x = -0.255 m
```

Robot konumları:

```text
left_arm:
    x = -0.255
    y = +0.200
    z = 0

right_arm:
    x = -0.255
    y = -0.200
    z = 0
```

Her ikisi de `+X` yönüne bakacak.

---

# 6. Ortak manipulation bölgesi

Kinematik overlap'ın tamamına object spawn etmeyeceğiz.

Güvenli başlangıç bölgesi:

```text
base line'dan forward:
0.18 – 0.38 m

table centerline:
-0.12 – +0.12 m
```

Yani yaklaşık:

# **20 cm × 24 cm**

core bimanual object zone.

World coordinate ile:

```text
X = [-0.075, +0.125]
Y = [-0.120, +0.120]
```

Bu alan iki kolun da rahat erişebildiği merkez bölge olacak.

Daha sonra controller gelişince spawn zone genişletilebilir.

---

# 7. Servo modeli

Burada gerçek LeRobot davranışını referans alacağız.

LeRobot SO follower motorları position mode'a alıyor ve varsayılan olarak:

```text
P = 16
I = 0
D = 32
```

yazıyor. Hedefler `Goal_Position` register'ına gidiyor, feedback ise `Present_Position` register'ından okunuyor. ([GitHub][8])

Resmi SO-101 MJCF dosyası ise bu servo için başlangıç fizik parametreleri sunuyor:

```text
damping      = 0.60
frictionloss = 0.052
armature     = 0.028

kp = 998.22
kv = 2.731
```

ve ayrıca ±0.5° backlash modeli içeriyor. Kaynak açıkça bu PD gain'lerinin LeRobot servo register değerlerinin birebir matematiksel karşılığı olmadığını belirtiyor; simülasyon için türetilmişler. 

Bunları başlangıç baseline'ı yapacağız.

Ancak MJCF:

```text
force range = ±2.94 N·m
```

kullanıyor. 

Bu yaklaşık 30 kg·cm 12 V servo sınıfına denk geliyor.

Biz 7.4 V modeli seçtiğimiz için bunu kullanmayacağız.

Bizim başlangıç hard torque limit:

# **±1.91 N·m**

olacak. ([Waveshare][9])

Ayrıca sadece constant torque clamp kullanmak yerine basitleştirilmiş torque-speed envelope:

```text
              |ω|
τmax(ω) = τstall × (1 - ───────)
                         ωfree
```

kullanacağız.

Burada:

```text
τstall = 1.91 Nm
ωfree  = 5.45 rad/s
```

Bu sayede servo stall noktasında yüksek torque üretirken no-load speed'e yaklaştığında üretilebilecek torque azalacak.

---

# 8. Backlash modeli

Backlash ayrı modellenmeli.

SO-101'in mevcut MJCF baseline'ı:

```text
±0.5°
```

slack tanımlıyor. 

Ayrıca gerçek STS3215 üzerinde topluluk ölçümlerinde yaklaşık `0.87°` mekanik backlash raporlanmış. Bu ölçüm üretici garantisi değil, gerçek cihaz testi olduğu için calibration referansı olarak faydalı. ([GitHub][10])

V1:

```text
backlash_half_width = 0.5°
```

ile başlayacak.

Yani direction reversal sırasında yaklaşık 1° toplam slack bandı bulunacak.

Bu değer config olacak.

---

# 9. Encoder modeli

Gerçek STS3215:

```text
4096 steps/revolution
```

olduğu için LSB:

```text
360 / 4096
= 0.087890625°
```

olacak. ([Waveshare][9])

Hem komut hem feedback bu resolution'a quantize edilecek.

Encoder pipeline:

```text
Genesis q_ground_truth
        ↓
calibration offset
        ↓
small electrical jitter
        ↓
4096-count quantization
        ↓
sample-and-hold
        ↓
transport latency
        ↓
q_measured
```

V1 default:

```text
encoder_resolution_bits : 12

encoder_lsb_deg          : 0.087890625

random_jitter_sigma      : 0.5 encoder count
                         ≈ 0.044°

sensor_latency_ms        : 5

sensor_latency_jitter_ms : 1
```

Buradaki `0.044°` random jitter ve latency değerleri **üretici tarafından yayınlanmış accuracy değerleri değildir**; V1 engineering baseline'ıdır.

Gerçek donanım edinildiğinde değiştirilmesi gereken ilk calibration parametreleridir.

Önemli nokta: simülasyondaki ana hata kaynağı Gaussian encoder noise olmayacak.

Ana sapmalar:

```text
backlash
servo tracking error
torque limitation
contact forces
friction
quantization
```

olacak.

Bu gerçek donanıma daha yakın.

---

# 10. Ground truth ve noisy ROS state

İstediğin değişiklik burada kesinleştiriliyor.

Her iki robot için **iki ayrı joint state** yayınlanacak.

Normal controller interface:

```text
/left_arm/joint_states
/right_arm/joint_states
```

Bunlar:

# **NOISY / SENSOR-LIKE**

olacak.

Yani burada position:

```text
simulated encoder measurement
```

olacak.

Ground truth:

```text
/sim/left_arm/ground_truth/joint_states
/sim/right_arm/ground_truth/joint_states
```

Bunlar:

# **EXACT GENESIS PHYSICAL STATE**

olacak.

Örneğin:

```text
ROS command = 0.500 rad

Genesis physical joint:
0.4937 rad

encoder pipeline:
0.4941 rad

ROS:

/left_arm/joint_states
    0.4941

/sim/left_arm/ground_truth/joint_states
    0.4937
```

şeklinde görülebilecek.

Bu özellikle controller tuning sırasında çok yararlı olacak.

---

# 11. ROS command interface

ROS ekosisteminde açılar için standart SI convention kullanılacak.

Yani interface **degree değil radian** olacak.

Controller:

```text
radians
```

gönderecek.

Debug/helper CLI istersek degree kabul edip radian'a çevirebilir.

Command topic:

```text
/left_arm/joint_targets
/right_arm/joint_targets
```

Mesaj:

```text
trajectory_msgs/msg/JointTrajectory
```

olacak.

V1'de tek trajectory point kullanacağız.

Joint sırası:

```text
shoulder_pan
shoulder_lift
elbow_flex
wrist_flex
wrist_roll
gripper
```

Örneğin kavramsal mesaj:

```text
joint_names:
  shoulder_pan
  shoulder_lift
  elbow_flex
  wrist_flex
  wrist_roll
  gripper

positions:
  q1 q2 q3 q4 q5 q6
```

Bu seçimle custom ROS message yazmak zorunda kalmıyoruz ve ileride gerçek trajectory execution'a genişleyebiliyoruz.

---

# 12. JointState içeriği

Noisy topic:

```text
sensor_msgs/msg/JointState
```

ile:

```text
name[]
position[]
velocity[]
```

yayınlayacak.

`effort` boş bırakılabilir.

Çünkü gerçek STS3215'te gerçek torque sensor bulunmuyor; `Present_Load` yaklaşık servo load feedback'idir. Gerçek torque gibi sunmak yanıltıcı olur. LeRobot/Feetech tarafında position, velocity, load, voltage, temperature/current register'ları bulunuyor. ([GitHub][11])

Ground truth tarafında ise istersek:

```text
position
velocity
effort
```

üçünü de dolduracağız.

Ground-truth effort Genesis'in gerçek generalized joint force'u olacak.

Genesis hem controller tarafından uygulanan force'u hem de contact/Coriolis dahil gerçek internal joint force'u okuyabiliyor. ([Genesis World][3])

---

# 13. TF

Standart TF robotun measured joint state'inden üretilecek.

Yani gerçek robottaki gibi:

```text
measured joint state
        ↓
robot_state_publisher
        ↓
/tf
```

olacak.

İki aynı robot olduğu için frame ID'leri ayrıştırılacak:

```text
left_arm/base_link
left_arm/shoulder_link
...

right_arm/base_link
right_arm/shoulder_link
...
```

Ground-truth debugging için duplicate TF tree kurmak yerine gerektiğinde ayrı simulation-state topic'leri kullanılacak.

---

# 14. ROS topic/service sözleşmesi

Controller için gereken minimum interface:

| Topic                                      | Type                              | Anlam                 |
| ------------------------------------------ | --------------------------------- | --------------------- |
| `/left_arm/joint_targets`                  | `trajectory_msgs/JointTrajectory` | Sol kol target        |
| `/right_arm/joint_targets`                 | `trajectory_msgs/JointTrajectory` | Sağ kol target        |
| `/left_arm/joint_states`                   | `sensor_msgs/JointState`          | Noisy sol feedback    |
| `/right_arm/joint_states`                  | `sensor_msgs/JointState`          | Noisy sağ feedback    |
| `/sim/left_arm/ground_truth/joint_states`  | `sensor_msgs/JointState`          | Exact sol state       |
| `/sim/right_arm/ground_truth/joint_states` | `sensor_msgs/JointState`          | Exact sağ state       |
| `/clock`                                   | `rosgraph_msgs/Clock`             | Simulation clock      |
| `/tf`                                      | standard TF                       | measured robot frames |
| `/tf_static`                               | standard TF                       | fixed frames          |

Simulation utilities:

```text
/sim/reset
/sim/pause
/sim/resume
/sim/spawn_object
/sim/delete_object
```

Bunlar controller contract'ın parçası olmayacak; simulation tooling olacak.

Ayrıca objelerin gerçek pozisyonlarını debugging için:

```text
/sim/ground_truth/objects
```

altında yayınlamak mantıklı.

Bu perception değildir; simulation-only debug bilgisi olacak.

---

# 15. Timing

V1 başlangıç frekansları:

```text
Genesis physics       : 500 Hz
servo update          : 100 Hz
controller nominal    : 50 Hz
ROS noisy joint state : 50 Hz
ground truth state    : 50 Hz
```

Physics:

```text
dt = 0.002 s
```

olacak.

Kontrolcü yeni target göndermezse servo gerçek position servo gibi **son target'ı tutmaya devam edecek**.

Command timeout robotu sıfıra göndermeyecek.

Sadece diagnostic:

```text
command stale
```

durumu üretilebilir.

Bütün frekanslar config'den değişebilir.

---

# 16. Gripper

SO-101'in önemli bir modelleme ayrıntısı var.

Mevcut URDF'de gripper:

```text
revolute joint
-0.1745 → 1.7453 rad
```

olarak modellenmiş. 

LeRobot ise kullanıcı seviyesinde gripper'ı:

```text
0   = closed
100 = open
```

şeklinde normalize ediyor ve SO-101 simulation README'si bu mapping'in URDF/MJCF'e henüz birebir aktarılmadığını açıkça söylüyor. ([GitHub][6])

ROS V1'de fiziksel anlamı koruyacağız:

```text
gripper joint target = radians
```

Kütüphanede ayrıca:

```text
lerobot_gripper_to_rad()
rad_to_lerobot_gripper()
```

helper fonksiyonları bulunacak.

Böylece daha sonra LeRobot compatibility kolay olur.

---

# 17. Objeler

Başlangıç object library:

```text
small_box
medium_box
cylinder
sphere
```

Önerilen defaultlar:

```text
small_box:
  40 × 40 × 40 mm
  mass: 50 g

medium_box:
  80 × 50 × 50 mm
  mass: 150 g

cylinder:
  diameter: 60 mm
  height: 80 mm
  mass: 100 g

sphere:
  diameter: 60 mm
  mass: 80 g
```

Her asset'in:

```text
size
mass
friction
restitution
initial pose
```

değeri config olacak.

Bimanual controller geliştirme açısından en önemli başlangıç objesi:

**80 × 50 × 50 mm kutu**

olacak.

İki kolun birlikte tutması, aktarması ve taşıması için yeterince büyük fakat SO-101 için hâlâ makul.

---

# 18. Contact/friction

Table ve object collision'ları primitive geometry olacak.

Robot visual mesh'leri detaylı kalırken physics contact basitleştirilecek.

Başlangıç friction değerleri deneysel olarak:

```text
table/object friction   ≈ 0.6
gripper/object friction ≈ 0.8
```

alınabilir.

Bunlar hardware-sourced parametre değildir.

Config içerisinde tutulacak ve gerçek gripper material'ı/masa yüzeyi belli olduğunda kalibre edilecek.

---

# 19. Genesis kullanımı

Genesis'in güncel sürümü CPU, CUDA, AMD ve Apple Metal backend'lerini destekliyor; GPU yoksa CPU'ya düşebiliyor. ([Genesis World][12])

Robot:

```python
gs.morphs.URDF(...)
```

ile import edilecek.

Source inertia korunacak:

```text
recompute_inertia = false
```

Collision için Genesis'in convexification/decimation seçeneklerini kontrollü kullanacağız. ([Genesis World][7])

Actuation:

```text
control_dofs_position()
```

üzerinden olacak.

Gerekli servo özelliklerini Genesis doğrudan destekliyor:

```text
kp
kv
force range
damping
friction loss
armature
```

([Genesis World][13])

Dolayısıyla kendi rigid-body solver veya PID physics engine'imizi yazmayacağız.

---

# 20. Hazır alacağımız parçalar

| Parça                               | Kaynak         |
| ----------------------------------- | -------------- |
| SO-101 CAD geometry                 | TheRobotStudio |
| STL visual mesh'leri                | TheRobotStudio |
| URDF                                | TheRobotStudio |
| joint origins                       | TheRobotStudio |
| joint limits                        | TheRobotStudio |
| masses                              | TheRobotStudio |
| inertia tensors                     | TheRobotStudio |
| başlangıç servo PD parametreleri    | SO-101 MJCF    |
| başlangıç friction/damping/armature | SO-101 MJCF    |
| başlangıç backlash modeli           | SO-101 MJCF    |
| rigid-body dynamics                 | Genesis        |
| contact solver                      | Genesis        |
| collision handling                  | Genesis        |
| PD actuator infrastructure          | Genesis        |
| ROS message definitions             | ROS 2          |
| robot_state_publisher               | ROS 2          |
| TF                                  | ROS 2          |
| simulation clock convention         | ROS 2          |

SO-101 asset'lerini runtime'da internetten çekmek yerine repository içine **pinned third-party asset** olarak koyacağız.

Kaynak commit hash'i ve lisans/attribution korunacak.

Bu reproducibility açısından önemli.

---

# 21. Bizim yazacağımız parçalar

Asıl proje:

```text
so101_bimanual_sim/
│
├── pyproject.toml
├── uv.lock
├── Dockerfile
├── compose.yaml
├── run.sh
│
├── config/
│   ├── simulation.yaml
│   ├── scene.yaml
│   ├── servo.yaml
│   ├── sensors.yaml
│   ├── objects.yaml
│   └── ros.yaml
│
├── third_party/
│   └── so101/
│       ├── urdf/
│       ├── meshes/
│       ├── SOURCE_COMMIT
│       └── LICENSE
│
├── src/
│   └── so101_sim/
│       │
│       ├── simulation/
│       │   ├── world.py
│       │   └── runner.py
│       │
│       ├── robot/
│       │   ├── so101.py
│       │   ├── actuator.py
│       │   ├── backlash.py
│       │   └── encoder.py
│       │
│       ├── scene/
│       │   ├── table.py
│       │   └── objects.py
│       │
│       └── ros/
│           ├── node.py
│           ├── commands.py
│           ├── joint_states.py
│           ├── ground_truth.py
│           └── sim_services.py
│
├── ros_ws/
│   └── src/
│       └── so101_sim_bringup/
│
└── tests/
    ├── test_fk.py
    ├── test_joint_limits.py
    ├── test_encoder.py
    ├── test_servo.py
    ├── test_ros_interface.py
    └── test_bimanual_workspace.py
```

---

# 22. Core class ayrımı

Simulation kodunun ROS'a bağımlı olmaması önemli.

Yaklaşık dependency direction:

```text
              ROS adapter
                  │
                  ▼
        Simulation interface
                  │
       ┌──────────┴──────────┐
       ▼                     ▼
 SO101Arm                 World
       │
       ▼
 ServoModel
       │
       ▼
 Genesis
```

Örneğin:

```text
SO101Arm.set_joint_targets()
SO101Arm.get_measured_state()
SO101Arm.get_ground_truth_state()
```

ROS node yalnızca bunları kullanacak.

Bu sayede yarın ROS yerine doğrudan Python RL environment yazmak istersek simulation core değişmez.

---

# 23. Config-first tasarım

Hardcoded fizik parametresi olmayacak.

Örneğin:

```yaml
robot:
  model: so101_follower

servo:
  model: sts3215_7_4v

  kp: 998.22
  kv: 2.731

  stall_torque_nm: 1.91
  no_load_speed_rad_s: 5.45

  damping: 0.60
  friction_loss: 0.052
  armature: 0.028

  backlash_deg: 0.5

encoder:
  bits: 12
  noise_sigma_counts: 0.5
  latency_ms: 5
  latency_jitter_ms: 1

simulation:
  physics_hz: 500
  servo_hz: 100

ros:
  controller_hz: 50
  joint_state_hz: 50
  ground_truth_hz: 50

scene:
  table:
    width: 1.30
    depth: 0.75
    thickness: 0.04
    height: 0.75

  arms:
    separation: 0.40
    rear_offset: 0.12
```

gibi olacak.

---

# 24. Tek komut deployment

Resmî kullanım Docker olacak.

Python dependency manager olarak Docker'ın içinde `uv` kullanılacak.

Genesis'in güncel repository'si de `uv` kullanımını destekliyor; güncel `genesis-world` Python `>=3.10,<3.14` gerektiriyor. ([GitHub][14])

Container tabanı:

```text
Ubuntu 24.04
ROS 2 Jazzy
Python 3.12
```

olacak.

`uv.lock` ile:

```text
Genesis
numpy
PyYAML
pytest
...
```

tam sürümleri kilitlenecek.

ROS paketleri apt/rosdep katmanında tutulacak.

ROS'un system Python paketlerinin venv'den görülebilmesi için uv environment:

```text
Python 3.12
venv + system-site-packages
```

şeklinde kurulacak.

Bu sayede:

```text
rclpy      ← ROS apt installation
genesis    ← uv environment
```

aynı process içinde import edilebilir.

---

## Tek kullanıcı komutu

Hedef:

```bash
./run.sh
```

Bu script:

```text
Docker var mı?
    ↓
image mevcut mu?
    ├─ hayır → build
    └─ evet
    ↓
container launch
    ↓
ROS workspace source
    ↓
Genesis launch
    ↓
ROS bridge start
```

yapacak.

Ek opsiyonlar:

```bash
./run.sh
./run.sh --headless
./run.sh --cpu
./run.sh --gpu
./run.sh --reset-build
```

olabilir.

Ama normal kullanıcı sadece:

```bash
./run.sh
```

bilmek zorunda.

---

# 25. CPU/GPU davranışı

Default:

```text
backend = auto
```

olacak.

Genesis mevcut cihazları CUDA → AMD → Metal → CPU sırasıyla değerlendirebiliyor ve kullanılabilir GPU yoksa CPU backend'ine düşüyor. ([Genesis World][12])

Dolayısıyla controller arkadaşına:

```text
"şu CUDA sürümünü yükle"
```

gibi zorunluluk getirmeyeceğiz.

İki küçük robot + masa + birkaç rigid object için CPU kullanılabilir.

Viewer/rendering performansı sorun olursa:

```bash
./run.sh --headless
```

ile physics + ROS tamamen devam edecek.

---

# 26. Reproducibility

Simülasyon sonuçlarının karşılaştırılabilmesi için:

```text
random_seed
```

config olacak.

Şunlar pinlenecek:

```text
Python version
Genesis version
Python dependencies
ROS distribution
SO101 asset commit
configuration
```

Güncel Genesis `pyproject.toml` sürümü şu anda `1.3.1`; implementation başladığında bunu `uv.lock` üzerinden tam sürüme sabitlemek mantıklı. ([GitHub][15])

`latest` branch'e runtime dependency olmayacak.

---

# 27. Testler

Projeyi yalnızca “ekranda robot hareket ediyor” diye tamamlanmış kabul etmeyeceğiz.

Minimum automated test suite:

### Kinematics test

URDF known poses ile bizim robot state eşleşmeli.

```text
q = 0
→ gripper ≈
x 0.391
y 0
z 0.226
```

regression test olacak.

### Encoder test

```text
4096 counts = 360°
1 count = 0.087890625°
```

doğrulanacak.

### Ground-truth separation

Test şunu doğrulayacak:

```text
measured_state != ground_truth_state
```

noise/backlash aktifken.

### Servo step response

Örneğin:

```text
q = 0
target = +30°
```

verildiğinde:

* instantaneous teleport olmamalı,
* velocity limit aşılmamalı,
* torque limit aşılmamalı,
* sonunda target yakınına yerleşmeli.

### Collision test

Kol masadan geçmemeli.

Gripper kutudan geçmemeli.

### Bimanual workspace test

Core object zone'dan seçilen noktalar her iki robot için de IK-reachable olmalı.

### ROS smoke test

Container açıldıktan sonra:

```text
/left_arm/joint_states
/right_arm/joint_states
/sim/.../ground_truth/...
/clock
```

yayında olmalı.

Target gönderildiğinde ilgili robot hareket etmeli.

---

# 28. V1 dışında bıraktığımız şeyler

Bunlar özellikle yapılmayacak:

```text
camera simulation
RGB-D
perception
tactile sensor
full motor thermal model
battery model
wire flexibility
plastic link compliance
motor-to-motor manufacturing variation
ROS2 Control integration
MoveIt integration
RL training API
photorealistic renderer
```

Bunların hiçbiri mevcut controller geliştirme amacı için V1 blocker değil.

Ancak mimari bunların sonradan eklenmesine engel olmayacak.

---

# 29. Gerçek robot geldiğinde yapılacak calibration

Bu simülasyonu “gerçekçi baseline”dan “gerçek robota kalibre edilmiş digital twin” seviyesine taşıyan son aşama bu olacak.

Her joint için gerçek robot üzerinde:

```text
step response
slow position sweep
direction reversal
loaded hold
free motion
```

ölçülür.

Kaydedilecek:

```text
q_target
q_measured
velocity
load/current
time
```

Sonra simde:

```text
kp
kv
friction
backlash
latency
torque curve
encoder jitter
```

fit edilir.

Bu aşamadan önce bu parametrelerin bazıları iyi kaynaklanmış baseline, bazıları engineering approximation olacaktır. Bunu gizlemek yerine config'te açıkça ayırmak doğru yaklaşım.

---

# 30. Son kilitlenmiş spesifikasyon

| Alan                   | Karar                                |
| ---------------------- | ------------------------------------ |
| Simulator              | Genesis                              |
| Robot                  | 2 × SO-101 follower                  |
| Motor                  | STS3215 7.4 V                        |
| Gear ratio             | 1:345                                |
| DOF                    | 5 arm + gripper / robot              |
| Control                | joint position                       |
| Controller             | external ROS 2                       |
| ROS distro             | Jazzy                                |
| OS                     | Ubuntu 24.04 container               |
| Python                 | 3.12                                 |
| Dependency management  | uv                                   |
| Deployment             | Docker                               |
| Normal start           | `./run.sh`                           |
| Physics                | 500 Hz                               |
| Servo model            | 100 Hz                               |
| Controller nominal     | 50 Hz                                |
| Joint feedback         | 50 Hz                                |
| Encoder                | 12 bit / 4096                        |
| Encoder LSB            | 0.08789°                             |
| Backlash initial       | ±0.5°                                |
| Torque limit           | ±1.91 N·m                            |
| No-load speed          | 5.45 rad/s                           |
| Servo baseline kp      | 998.22                               |
| Servo baseline kv      | 2.731                                |
| Damping                | 0.60                                 |
| Friction loss          | 0.052                                |
| Armature               | 0.028                                |
| Table                  | 1.30 × 0.75 m                        |
| Table height           | 0.75 m                               |
| Arm separation         | 0.40 m                               |
| Base rear offset       | 0.12 m                               |
| Main spawn zone        | 0.20 × 0.24 m                        |
| Cameras                | None                                 |
| Main ROS state         | simulated/noisy                      |
| Ground truth ROS state | also published                       |
| Main command units     | radians                              |
| ROS bridge             | our thin `rclpy` adapter             |
| ros2_control           | not V1 dependency                    |
| Objects                | box/cylinder/sphere                  |
| Bimanual physics       | same Genesis world                   |
| Visuals                | original SO-101 meshes               |
| Collision              | optimized separately                 |
| Config                 | all fidelity parameters externalized |
| Reproducibility        | versions + assets + seed pinned      |

Bu haliyle proje tanımı artık implementasyona başlanabilecek kadar kesin: en kritik abstraction'lar, referans donanım, masa ve robot yerleşimi, ROS contract'ı, noisy/ground-truth ayrımı, servo/encoder gerçekçilik modeli, frekanslar ve deployment yöntemi belirlenmiş durumda.

[1]: https://github.com/huggingface/lerobot/blob/main/docs/source/so101.mdx?utm_source=chatgpt.com "lerobot/docs/source/so101.mdx at main · huggingface/lerobot · GitHub"
[2]: https://www.waveshare.com/product/modules/st3215-servo.htm?utm_source=chatgpt.com "ST3215 Series Serial Bus Servo, High precision and torque, 360 Degrees Magnetic Encoder, Two-way Feedback, Servo/Motor Mode Switchable, Options For 30kg.cm@12V / 19.5kg.cm@7.4V Torque | ST3215 Servo"
[3]: https://genesis-world.readthedocs.io/en/latest/user_guide/getting_started/control_your_robot.html?utm_source=chatgpt.com "Control your robot — Genesis World"
[4]: https://github.com/signalbotics/genesis_ros?utm_source=chatgpt.com "GitHub - signalbotics/genesis_ros: ROS 2 bridge for the Genesis physics simulator + Debian packaging for Ubuntu 24.04 / Jazzy. · GitHub"
[5]: https://docs.ros.org/en/jazzy/Installation/Alternatives/Ubuntu-Install-Binary.html?utm_source=chatgpt.com "Ubuntu (binary) — ROS 2 Documentation: Jazzy documentation"
[6]: https://github.com/TheRobotStudio/SO-ARM100/blob/main/Simulation/SO101/README.md?utm_source=chatgpt.com "SO-ARM100/Simulation/SO101/README.md at main · TheRobotStudio/SO-ARM100 · GitHub"
[7]: https://genesis-world.readthedocs.io/en/latest/api_reference/engine/entity/morph/file_morph/urdf.html?utm_source=chatgpt.com "URDF — Genesis World"
[8]: https://github.com/huggingface/lerobot/blob/main/src/lerobot/robots/so_follower/so_follower.py?utm_source=chatgpt.com "lerobot/src/lerobot/robots/so_follower/so_follower.py at main · huggingface/lerobot · GitHub"
[9]: https://www.waveshare.com/product/st3215-servo.htm?utm_source=chatgpt.com "ST3215 Series Serial Bus Servo, High precision and torque, 360 Degrees Magnetic Encoder, Two-way Feedback, Servo/Motor Mode Switchable, Options For 30kg.cm@12V / 19.5kg.cm@7.4V Torque | ST3215 Servo"
[10]: https://github.com/TheRobotStudio/SO-ARM100/issues/134?utm_source=chatgpt.com "Feetech STS3215 servos has around 1 degree real backlash · Issue #134 · TheRobotStudio/SO-ARM100 · GitHub"
[11]: https://github.com/huggingface/lerobot/blob/main/src/lerobot/motors/feetech/tables.py?utm_source=chatgpt.com "lerobot/src/lerobot/motors/feetech/tables.py at main · huggingface/lerobot · GitHub"
[12]: https://genesis-world.readthedocs.io/en/latest/user_guide/configuration/initialization.html?utm_source=chatgpt.com "Initialization and backends — Genesis World"
[13]: https://genesis-world.readthedocs.io/en/latest/api_reference/engine/entity/rigid_entity/rigid_entity.html?utm_source=chatgpt.com "RigidEntity — Genesis World"
[14]: https://github.com/Genesis-Embodied-AI/Genesis?utm_source=chatgpt.com "GitHub - Genesis-Embodied-AI/Genesis: A generative world for general-purpose robotics & embodied AI learning. · GitHub"
[15]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/main/pyproject.toml?utm_source=chatgpt.com "genesis-world/pyproject.toml at main · Genesis-Embodied-AI/genesis-world · GitHub"
