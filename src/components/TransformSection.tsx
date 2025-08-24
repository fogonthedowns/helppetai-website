import React from 'react';

const TransformSection = () => {
  return (
    <section className="bg-white py-16 w-full overflow-hidden">
      <div className="max-w-7xl mx-auto px-6">
        {/* Title */}
        <div className="text-center mb-16">
          <h2 className="text-5xl lg:text-6xl font-bold text-gray-900 mb-4" style={{
            fontFamily: 'Calibre, ui-sans-serif, system-ui, -apple-system, "system-ui", "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans", sans-serif'
          }}>
            Tail-Wagging Transformations
          </h2>
        </div>

        {/* Main Content Grid */}
        <div className="relative">
          {/* Statistics Boxes */}
          
          {/* 70% Box - Top Left */}
          <div className="absolute top-0 left-0 lg:left-8 transform -rotate-2 z-10">
            <div className="bg-green-500 rounded-2xl p-8 w-64 h-48 flex flex-col justify-center items-center relative shadow-lg border-4 border-gray-800 transform hover:scale-105 transition-transform duration-300">
              <div className="text-6xl font-black text-gray-800 mb-2">Faster</div>
              <div className="text-lg font-semibold text-gray-800">check-ins</div>
              
              {/* Decorative dots */}
              <div className="absolute top-4 right-4 w-3 h-3 bg-gray-800 rounded-full opacity-30"></div>
              <div className="absolute bottom-4 left-4 w-2 h-2 bg-gray-800 rounded-full opacity-30"></div>
            </div>
          </div>

          {/* 50% Box - Bottom Left */}
          <div className="absolute top-40 left-4 lg:left-16 transform rotate-1 z-10">
            <div className="bg-blue-600 rounded-2xl p-8 w-64 h-48 flex flex-col justify-center items-center relative shadow-lg border-4 border-gray-800 transform hover:scale-105 transition-transform duration-300">
              <div className="text-6xl font-black text-white mb-2">Expert</div>
              <div className="text-lg font-semibold text-white">AI</div>
              
              {/* Decorative dots */}
              <div className="absolute top-4 right-4 w-3 h-3 bg-white rounded-full opacity-30"></div>
              <div className="absolute bottom-4 left-4 w-2 h-2 bg-white rounded-full opacity-30"></div>
            </div>
          </div>

          {/* 1-2 hrs Box - Top Right */}
          <div className="absolute top-12 right-0 lg:right-8 transform rotate-2 z-10">
            <div className="bg-amber-400 rounded-2xl p-8 w-72 h-56 flex flex-col justify-center items-center relative shadow-lg border-4 border-gray-800 transform hover:scale-105 transition-transform duration-300">
              <div className="text-5xl font-black text-gray-800 mb-2">Automate</div>
              <div className="text-base font-semibold text-gray-800 text-center leading-tight">SOAP</div>
              
              {/* Simple decorative dots */}
              <div className="absolute top-4 right-4 w-3 h-3 bg-gray-800 rounded-full opacity-30"></div>
              <div className="absolute bottom-4 left-4 w-2 h-2 bg-gray-800 rounded-full opacity-30"></div>
              

            </div>
          </div>

          {/* Animated Dog - Bottom Right Center */}
          <div className="flex justify-center items-end h-64 lg:h-80 relative z-0">
            <div className="absolute bottom-8 right-1/3 transform translate-x-1/3">
              <img 
                src="/dachshund-dog.gif" 
                alt="Animated Dachshund Dog" 
                className="w-[500px] h-[500px] object-contain"
                style={{ 
                  imageRendering: 'auto',
                  animation: 'none' /* Ensure no CSS overrides the gif loop */
                }}
                onLoad={(e) => {
                  /* Force gif to loop if it's not already */
                  const img = e.target as HTMLImageElement;
                  if (img.complete) {
                    img.style.animation = 'none';
                  }
                }}
              />
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default TransformSection;
