package com.example.joljak

import android.app.AlertDialog
import android.os.Bundle
import android.content.Intent
import android.app.DatePickerDialog
import android.content.Context
import android.graphics.Color
import android.graphics.drawable.ColorDrawable
import android.util.Log
import android.widget.SeekBar
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import com.example.joljak.comm.SearchRequest
import com.example.joljak.comm.*
import com.example.joljak.comm.SearchResponse
import com.example.joljak.databinding.ActivitySetDataBinding
import com.google.android.material.button.MaterialButton
import com.google.android.material.button.MaterialButtonToggleGroup
import com.google.android.material.datepicker.MaterialDatePicker
import com.google.android.material.slider.Slider
import retrofit2.Call
import retrofit2.Callback
import retrofit2.Response
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import java.text.SimpleDateFormat
import java.util.*
import androidx.core.util.Pair

class SetData : AppCompatActivity() {

    private lateinit var binding: ActivitySetDataBinding
    private lateinit var startDate:String
    private lateinit var finishDate:String

    fun showLoadingDialog(context: Context): AlertDialog {
        val builder = AlertDialog.Builder(context)
        builder.setView(R.layout.loading_dialog)
        builder.setCancelable(false) // 다이얼로그 바깥을 터치해도 닫히지 않도록 설정
        return builder.create()
    }
    override fun onBackPressed() {
        super.finish()
        finish() // 현재 액티비티를 종료
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        // ViewBinding 초기화
        binding = ActivitySetDataBinding.inflate(layoutInflater)
        setContentView(binding.root)

        // Retrofit 초기
        // 화
        val retrofit = Retrofit.Builder()
            .baseUrl("http:///192.168.0.8:5000/")
            .addConverterFactory(GsonConverterFactory.create())
            .build()

        val apiService = retrofit.create(SearchApiInterface::class.java)

        binding.Search.setOnClickListener {
            val age = binding.ageSliderValueText.text.toString()
            // 성별과 View 값을 가져오기
            val genderToggleGroup = findViewById<MaterialButtonToggleGroup>(R.id.genderToggleGroup)
            val selectedGenderButtonId = genderToggleGroup.checkedButtonId
            val selectedGenderButton = findViewById<MaterialButton>(selectedGenderButtonId)
            val selectedGender = selectedGenderButton.text.toString()

            val viewToggleGroup = findViewById<MaterialButtonToggleGroup>(R.id.viewToggleGroup)
            val selectedViewButtonId = viewToggleGroup.checkedButtonId
            val selectedViewButton = findViewById<MaterialButton>(selectedViewButtonId)

            val selectedView = when(selectedViewButton.text.toString()) {
                "Few" -> "4"
                "Medium" -> "7"
                "Many" -> "15"
                else -> "5" // 기본값 혹은 예외 처리
            }

            // 성별과 View 값을 로그로 출력
            Log.d("SelectedValues", "Selected Gender: $selectedGender")
            Log.d("SelectedValues", "Selected View: $selectedView")
            val gender = selectedGender
            val view = selectedView
            val people = binding.sliderValueText.text.toString() // 수정된 부분: 슬라이더 값을 가져오도록 수정

            val request = SearchRequest(age, gender, startDate, finishDate, view, people) // 수정된 부분: people 값을 추가

            val loadingDialog=showLoadingDialog(this)
            loadingDialog.show()
            loadingDialog.window?.setBackgroundDrawable(ColorDrawable(Color.TRANSPARENT)) // 팝업 배경을 투명하게 설정

            val call = apiService.search(request)
            call.enqueue(object : Callback<SearchResponse> {
                override fun onResponse(call: Call<SearchResponse>, response: Response<SearchResponse>) {
                    loadingDialog.dismiss()
                    if (response.isSuccessful) {
                        val responseBody = response.body()
                        Log.d("SetData", "Response: ${responseBody?.status}")
                        Log.d("SetData", "Full Response: $responseBody")

                        Log.d("IntentData", "AGE: $age")
                        Log.d("IntentData", "GENDER: $gender")
                        Log.d("IntentData", "START_DATE: $startDate")
                        Log.d("IntentData", "FINISH_DATE: $finishDate")
                        Log.d("IntentData", "PEOPLE: $people") // 수정된 부분: people 값을 로그로 출력

                        val carDataList = responseBody?.cars
                        val carNamesList: ArrayList<String> = ArrayList(carDataList?.flatMap { it.names } ?: listOf())

                        val intent = Intent(this@SetData, CarList::class.java)
                        intent.putExtra("AGE", age)
                        intent.putExtra("GENDER", gender)
                        intent.putExtra("START_DATE", startDate)
                        intent.putExtra("FINISH_DATE", finishDate)
                        intent.putExtra("PEOPLE", people) // 수정된 부분: people 값을 인텐트로 전달
                        intent.putStringArrayListExtra("CAR_NAMES", carNamesList)
                        intent.putExtra("CAR_DATA_LIST", ArrayList(responseBody?.cars))
                        startActivity(intent)

                    } else {
                        Log.d("SetData", "Response Failed")
                    }
                }

                override fun onFailure(call: Call<SearchResponse>, t: Throwable) {
                    loadingDialog.dismiss()
                    Log.d("SetData", "Request Failed: ${t.message}")
                }
            })
        }



        binding.numberOfPeopleSlider.addOnChangeListener { slider, value, fromUser ->
            // 슬라이더 값이 변경될 때마다 TextView에 표시
            binding.sliderValueText.text = value.toInt().toString()
        }
        binding.ageSlider.addOnChangeListener { slider, value, fromUser ->
            // 슬라이더 값이 변경될 때마다 TextView에 표시
            binding.ageSliderValueText.text = value.toInt().toString()
        }
        binding.dateRange.setOnClickListener {
            showDateRangePicker()
        }


    }
    private fun showDateRangePicker() {
        // 날짜 범위 선택기 생성
        val dateRangePicker = MaterialDatePicker.Builder.dateRangePicker()
            .setTitleText("Select dates")
            .build()

        // 선택기를 보여줌
        dateRangePicker.show(supportFragmentManager, "date_range_picker")

        // 사용자가 날짜를 선택하면 결과 처리
        dateRangePicker.addOnPositiveButtonClickListener { dateRange ->
            val typedstartdate = dateRange.first
            val typedenddate = dateRange.second
            if (typedstartdate != null && typedenddate != null) {
                // 날짜 포맷 지정
                val formatter = SimpleDateFormat("yyyy/MM/dd", Locale.getDefault())
                val formattedStartDate = formatter.format(Date(typedstartdate))
                val formattedEndDate = formatter.format(Date(typedenddate))
                startDate = formattedStartDate
                finishDate = formattedEndDate
                binding.dateRange.setText("$formattedStartDate - $formattedEndDate")

            }
        }
    }
}
