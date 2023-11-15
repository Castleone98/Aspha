package com.example.joljak

import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.ImageView
import android.widget.TextView
import androidx.recyclerview.widget.RecyclerView
import com.bumptech.glide.Glide
import com.example.joljak.comm.CarData
import com.example.joljak.comm.CarNameWithFuelType

class CarAdapter(private val carList: List<CarNameWithFuelType>) : RecyclerView.Adapter<CarAdapter.ViewHolder>() {

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): ViewHolder {
        val view = LayoutInflater.from(parent.context).inflate(R.layout.item_car, parent, false)
        return ViewHolder(view)
    }

    override fun onBindViewHolder(holder: ViewHolder, position: Int) {
        val car = carList[position]
        holder.carName.text = car.name
        holder.fuelType.text = "Fuel Type: ${car.fuelType}"

        // 이미지 로드 및 표시
        car.imageUrl?.let { imageUrl ->
            // 이미지 로딩 라이브러리 사용 (예: Glide)
            Glide.with(holder.itemView.context)
                .load(imageUrl)
                .into(holder.carImage)
        }
    }

    class ViewHolder(view: View) : RecyclerView.ViewHolder(view) {
        val carName: TextView = view.findViewById(R.id.carName)
        val fuelType: TextView = view.findViewById(R.id.fuelType)
        val carImage: ImageView = view.findViewById(R.id.carImage) // ImageView 참조 추가
    }

    override fun getItemCount() = carList.size
}

