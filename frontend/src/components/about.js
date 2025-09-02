import React from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { motion } from "framer-motion";

const AboutUs = () => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 to-gray-800 text-white flex flex-col items-center p-8">
      <motion.h1
        className="text-4xl font-bold mb-6 text-center"
        initial={{ opacity: 0, y: -30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.7 }}
      >
        About Us
      </motion.h1>

      <Card className="max-w-3xl bg-gray-700/40 backdrop-blur-md shadow-xl rounded-2xl">
        <CardContent className="p-6">
          <motion.p
            className="text-lg leading-relaxed mb-4"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.3 }}
          >
            Welcome to <span className="font-semibold text-blue-400">AI-Based Code Debugger</span>,
            your intelligent coding companion. Our mission is to empower developers by providing
            real-time debugging assistance, code optimization suggestions, and AI-powered insights
            to make programming faster and smarter.
          </motion.p>

          <motion.p
            className="text-lg leading-relaxed mb-4"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.6 }}
          >
            We are passionate about bridging the gap between human creativity and artificial
            intelligence. With a focus on accuracy, usability, and innovation, we aim to revolutionize
            the way developers debug and enhance their code.
          </motion.p>

          <motion.p
            className="text-lg leading-relaxed"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.9 }}
          >
            Join us on our journey to build the future of coding with AI. Whether you are a student,
            beginner, or experienced professional, our platform is designed to support you at every
            stage of development.
          </motion.p>

          <div className="mt-6 flex justify-center">
            <Button className="px-6 py-2 text-lg rounded-2xl bg-blue-500 hover:bg-blue-600 transition">
              Learn More
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default AboutUs;
