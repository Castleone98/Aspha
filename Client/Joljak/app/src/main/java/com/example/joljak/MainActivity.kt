package com.example.joljak


import android.os.Bundle
import androidx.appcompat.app.AppCompatActivity
import com.example.joljak.databinding.ActivityMainBinding
import android.content.Intent

class MainActivity : AppCompatActivity() {

    private lateinit var binding: ActivityMainBinding

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)
        setSupportActionBar(binding.toolbar)

        binding.button.setOnClickListener {
            val intent = Intent(this, SetData::class.java)
            startActivity(intent)
        }
    }
}
