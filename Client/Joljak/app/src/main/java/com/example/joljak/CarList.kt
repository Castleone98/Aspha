package com.example.joljak

import androidx.appcompat.app.AppCompatActivity
import android.os.Bundle
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import android.util.Log
import android.widget.TextView
import com.example.joljak.comm.CarData
import com.example.joljak.comm.CarNameWithFuelType
import com.example.joljak.comm.NaverSearchAPI
import com.example.joljak.comm.NaverSearchResponse
import retrofit2.Call
import retrofit2.Callback
import retrofit2.Response
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory

class CarList : AppCompatActivity() {


    private lateinit var recyclerView: RecyclerView
    private lateinit var adapter: CarAdapter
    private val carList = mutableListOf<CarNameWithFuelType>()  // 타입을 MutableList<CarNameWithFuelType>으로 변경

    override fun onBackPressed() {
        super.finish()
        finish() // 현재 액티비티를 종료
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_car_list)

        // Intent로부터 데이터를 가져옵니다.
        val age = intent.getStringExtra("AGE")
        val gender = intent.getStringExtra("GENDER")
        val startDate = intent.getStringExtra("START_DATE")
        val finishDate = intent.getStringExtra("FINISH_DATE")
        val carsFromIntent: List<CarData> = intent.getSerializableExtra("CAR_DATA_LIST") as List<CarData>

        recyclerView = findViewById(R.id.recyclerView)
        recyclerView.layoutManager = LinearLayoutManager(this)
        adapter = CarAdapter(carList)
        recyclerView.adapter = adapter

        // 로그로 차량 데이터 출력
        carsFromIntent.forEach { Log.d("CarList", it.toString()) }

        // 차량 데이터 로드
        loadCars(carsFromIntent)

    }

    // Retrofit과 NaverSearchAPI 인터페이스를 사용하여 네이버 검색 API 호출
    private fun searchImageFromNaver(query: String, car: CarNameWithFuelType, display: Int = 1) {
        val retrofit = Retrofit.Builder()
            .baseUrl("https://openapi.naver.com")
            .addConverterFactory(GsonConverterFactory.create())
            .build()

        val naverSearchAPI = retrofit.create(NaverSearchAPI::class.java)

        // API 호출
        naverSearchAPI.searchImages("r4wCV58pBXQKjbpME_U9", "_zO1OX93v8", query, display).enqueue(object : Callback<NaverSearchResponse> {
            override fun onResponse(call: Call<NaverSearchResponse>, response: Response<NaverSearchResponse>) {
                if (response.isSuccessful) {
                    // 첫 번째 non-null 이미지 URL 찾기
                    val imageUrl = response.body()?.items?.firstOrNull { it.thumbnail != null }?.thumbnail
                    if (imageUrl != null) {
                        car.imageUrl = imageUrl // 이미지 URL 저장
                        runOnUiThread {
                            adapter.notifyDataSetChanged() // 어댑터에 데이터 변경 알림
                        }
                    } else if (display < MAX_DISPLAY_LIMIT) {
                        searchImageFromNaver(query, car, display + 1) // display 값을 증가시키며 재시도
                    }
                    Log.d("CarList", "Image URL: ${imageUrl}")
                } else {
                    Log.e("CarList", "Response not successful")
                    if (display < MAX_DISPLAY_LIMIT) {
                        searchImageFromNaver(query, car, display + 1) // display 값을 증가시키며 재시도
                    }
                }
            }

            override fun onFailure(call: Call<NaverSearchResponse>, t: Throwable) {
                Log.e("CarList", "API call failed")
                if (display < MAX_DISPLAY_LIMIT) {
                    searchImageFromNaver(query, car, display + 1) // display 값을 증가시키며 재시도
                }
            }
        })
    }

    companion object {
        private const val MAX_DISPLAY_LIMIT = 15 // 최대 display 값 설정
    }


    private fun loadCars(carsFromIntent: List<CarData>) {
        carList.clear()
        carsFromIntent.forEach { carData ->
            carData.names.forEach { name ->
                val (carName, fuelType) = parseCarName(name)
                val car = CarNameWithFuelType(carName, fuelType,null)
                carList.add(car)
                searchImageFromNaver(parseCarNameForSearch(name), car)
            }
        }
    }


    private fun parseCarName(fullName: String): Pair<String, String> {
        val nameParts = fullName.split(" (")
        val name = nameParts[0]
        val fuelType = nameParts.getOrNull(1)?.removeSuffix(")") ?: "Unknown"
        return Pair(name, fuelType)
    }

    private fun parseCarNameForSearch(fullName: String): String {
        // 괄호와 그 안의 내용 제거
        val nameWithoutParentheses = fullName.split(" (")[0]
        // "X인" 형태의 부분 제거
        val nameParts = nameWithoutParentheses.split(" ")
        return if (nameParts.any { it.matches(Regex("\\d+인")) }) {
            nameParts.filterNot { it.matches(Regex("\\d+인")) }.joinToString(" ")
        } else {
            nameWithoutParentheses
        }
    }

}
