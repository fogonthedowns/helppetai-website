import React from 'react';
import { Link } from 'react-router-dom';
import { Heart, Users, Shield, Award, Stethoscope, Brain } from 'lucide-react';

// Import founder images from public folder
const JustinImage = '/justin.png';
const RobynneImage = '/robynne.jpg';

const AboutUs = () => {
  return (
    <div className="min-h-screen bg-white">
      {/* Hero Section */}
      <section className="bg-gradient-to-br from-blue-50 to-indigo-50 py-20">
        <div className="max-w-4xl mx-auto px-6 text-center">
          <h1 className="text-6xl font-bold text-gray-900 mb-6" style={{
            fontFamily: 'Calibre, ui-sans-serif, system-ui, -apple-system, "system-ui", "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans", sans-serif'
          }}>
            About HelpPetAI
          </h1>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto leading-relaxed">
          We're revolutionizing pet healthcare by making expert veterinary knowledge instantly accessible to the world.
          </p>
        </div>
      </section>

      {/* Mission Section */}
      <section className="py-16 bg-white">
        <div className="max-w-6xl mx-auto px-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
            <div>
              <h2 className="text-4xl font-bold text-gray-900 mb-6" style={{
                fontFamily: 'Calibre, ui-sans-serif, system-ui, -apple-system, "system-ui", "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans", sans-serif'
              }}>
                Our Mission
              </h2>
              <p className="text-lg text-gray-600 mb-6 leading-relaxed">
                Every pet deserves quality healthcare, but traditional veterinary care can be expensive and inaccessible. We believe that technology can bridge this gap by providing intelligent triage, connecting pet parents with the right level of care, and making veterinary expertise available when you need it most.
              </p>
              <p className="text-lg text-gray-600 leading-relaxed">
                Our AI-powered platform ensures your pet gets the appropriate care for their condition - from simple home treatments to specialist referrals - saving you time, money, and stress.
              </p>
            </div>
            <div className="flex justify-center">
              <div className="w-80 h-80 bg-gradient-to-br from-blue-100 to-purple-100 rounded-3xl flex items-center justify-center">
                <Heart className="w-32 h-32 text-blue-600" />
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Founders Section */}
      <section className="py-16 bg-gray-50">
        <div className="max-w-6xl mx-auto px-6">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-gray-900 mb-4" style={{
              fontFamily: 'Calibre, ui-sans-serif, system-ui, -apple-system, "system-ui", "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans", sans-serif'
            }}>
              Our Founders
            </h2>
            <p className="text-xl text-gray-600">Meet the team behind HelpPetAI</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-12 max-w-4xl mx-auto">
            {(() => {
              const teamMembers = [
                {
                  name: 'Justin Zollars',
                  role: 'Machine Learning Engineer',
                  bio: 'Machine learning engineer with experience building predictive models and PyTorch-based systems at Eat Just. Specialized in applied AI, and production ML pipelines that translate complex data into actionable insights for real-world applications.',
                  avatar: 'J',
                  image: JustinImage,
                },
                {
                  name: 'Robynne Merguerdijian',
                  role: 'Information Engineer',
                  bio: 'Information architect who curates and structures veterinary knowledge for our Expert AI system. Transforms complex medical research, clinical studies, and treatment protocols into accessible data that powers evidence-based pet care recommendations.',
                  avatar: 'R',
                  image: RobynneImage,
                },
              ];

              return teamMembers.map((member, index) => (
                <div key={index} className="bg-white rounded-2xl p-8 shadow-sm text-center">
                  <div className="mb-6">
                    <img
                      src={member.image}
                      alt={member.name}
                      className="w-32 h-32 rounded-full mx-auto object-cover mb-4"
                      onError={(e) => {
                        // Fallback to avatar if image fails to load
                        const target = e.target as HTMLImageElement;
                        target.style.display = 'none';
                        const fallback = target.nextElementSibling as HTMLElement;
                        if (fallback) fallback.style.display = 'flex';
                      }}
                    />
                    <div className="w-32 h-32 bg-blue-600 rounded-full mx-auto flex items-center justify-center text-white text-4xl font-bold hidden">
                      {member.avatar}
                    </div>
                  </div>
                  <h3 className="text-2xl font-bold text-gray-900 mb-2">{member.name}</h3>
                  <p className="text-lg text-blue-600 font-semibold mb-4">{member.role}</p>
                  <p className="text-gray-600 leading-relaxed">{member.bio}</p>
                </div>
              ));
            })()}
          </div>
        </div>
      </section>

      {/* Team Section */}
      <section className="py-16 bg-white">
        <div className="max-w-6xl mx-auto px-6">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-gray-900 mb-4" style={{
              fontFamily: 'Calibre, ui-sans-serif, system-ui, -apple-system, "system-ui", "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans", sans-serif'
            }}>
              Our Expertise
            </h2>
            <p className="text-xl text-gray-600">Combining technology with veterinary excellence</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-12 items-center">
            <div>
              <div className="space-y-8">
                <div className="flex items-start space-x-4">
                  <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center flex-shrink-0">
                    <Stethoscope className="w-6 h-6 text-blue-600" />
                  </div>
                  <div>
                    <h3 className="text-xl font-bold text-gray-900 mb-2">Licensed Veterinarians</h3>
                    <p className="text-gray-600">
                      Our network includes over 200 licensed veterinarians across all 50 states, each with expertise in different specialties.
                    </p>
                  </div>
                </div>

                <div className="flex items-start space-x-4">
                  <div className="w-12 h-12 bg-green-100 rounded-xl flex items-center justify-center flex-shrink-0">
                    <Users className="w-6 h-6 text-green-600" />
                  </div>
                  <div>
                    <h3 className="text-xl font-bold text-gray-900 mb-2">AI Development Team</h3>
                    <p className="text-gray-600">
                      Our engineers and data scientists have trained our AI on millions of veterinary cases to provide accurate triage and treatment recommendations.
                    </p>
                  </div>
                </div>

                <div className="flex items-start space-x-4">
                  <div className="w-12 h-12 bg-purple-100 rounded-xl flex items-center justify-center flex-shrink-0">
                    <Award className="w-6 h-6 text-purple-600" />
                  </div>
                  <div>
                    <h3 className="text-xl font-bold text-gray-900 mb-2">Expert Knowledge Base</h3>
                    <p className="text-gray-600">
                    Trained on comprehensive veterinary literature, clinical studies, and expert protocols to provide evidence-based pet healthcare guidance.
                    </p>
                  </div>
                </div>
              </div>
            </div>

            <div className="flex justify-center">
              <div className="w-96 h-96 bg-gradient-to-br from-blue-600 to-purple-600 rounded-3xl flex items-center justify-center">
                <div className="text-center text-white">
                  <div className="text-6xl font-bold mb-2">85%</div>
                  <div className="text-xl font-light">Cut your vet bills</div>
                  <div className="text-4xl font-bold mt-6 mb-2">15k+</div>
                  <div className="text-xl font-light">Hours saved</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="bg-blue-600 py-16">
        <div className="max-w-4xl mx-auto px-6 text-center">
          <h2 className="text-4xl font-bold text-white mb-6">
            Ready to get started?
          </h2>
          <p className="text-xl text-blue-100 mb-8">
            Join thousands of pet parents who trust HelpPetAI for their pet's healthcare needs.
          </p>
          <Link to="/vets" className="bg-white text-blue-600 px-8 py-4 rounded-lg text-lg font-bold hover:bg-gray-100 transition-colors">
            Start your pet's assessment
          </Link>
        </div>
      </section>
    </div>
  );
};

export default AboutUs;
