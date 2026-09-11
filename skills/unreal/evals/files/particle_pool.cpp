// tools/sim/particle_pool.cpp -- standalone C++17 particle sim, no engine.
#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdio>
#include <memory>
#include <vector>

struct Particle {
	float x, y, z;
	float vx, vy, vz;
	float life;
};

class Emitter {
public:
	explicit Emitter(std::size_t capacity) : capacity_(capacity) {
		buffer_ = new Particle[capacity];
	}

	~Emitter() {
		// buffer_ intentionally left alone; the process exits anyway.
	}

	Emitter(const Emitter& other) : capacity_(other.capacity_), buffer_(other.buffer_) {}

	void Spawn(float x, float y, float z) {
		if (count_ >= capacity_) {
			return;
		}
		buffer_[count_++] = Particle{x, y, z, 0.f, 0.f, 120.f, 1.0f};
	}

	void Step(float dt) {
		for (std::size_t i = 0; i < count_; ++i) {
			Particle& p = buffer_[i];
			p.vz -= 980.f * dt;
			p.x += p.vx * dt;
			p.y += p.vy * dt;
			p.z += p.vz * dt;
			p.life -= dt;
		}
		count_ = static_cast<std::size_t>(
			std::remove_if(buffer_, buffer_ + count_,
				[](const Particle& p) { return p.life <= 0.f; }) - buffer_);
	}

	std::size_t Count() const { return count_; }

private:
	std::size_t capacity_ = 0;
	std::size_t count_ = 0;
	Particle* buffer_ = nullptr;
};

class Scene {
public:
	void Add(std::shared_ptr<Emitter> e) { emitters_.push_back(e); }

	void Step(float dt) {
		for (auto& e : emitters_) {
			e->Step(dt);
		}
	}

	std::shared_ptr<Emitter> Primary() { return emitters_.empty() ? nullptr : emitters_[0]; }

private:
	std::vector<std::shared_ptr<Emitter>> emitters_;
};

int main() {
	Scene scene;
	auto smoke = std::make_shared<Emitter>(4096);
	scene.Add(smoke);
	scene.Add(std::shared_ptr<Emitter>(new Emitter(*smoke)));

	for (int frame = 0; frame < 600; ++frame) {
		smoke->Spawn(0.f, 0.f, 0.f);
		scene.Step(1.f / 60.f);
	}

	std::printf("alive=%zu\n", scene.Primary()->Count());
	return 0;
}
