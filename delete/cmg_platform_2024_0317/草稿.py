<div id="app">
    <el-form label-width="150px"> <!-- 统一设置 label 的宽度 -->
        <el-form-item>
            <el-button type="primary" @click="clickTrainData">训练数据</el-button>
            <el-button type="success" @click="clickTestData">测试数据</el-button>
        </el-form-item>

        <!-- Training Options -->
        <div v-if="showTrainOptions">
            <el-form-item label="选择训练数据">
                <el-select v-model="trainingDataPath" placeholder="请选择训练数据" style="width: 300px;">
                    <el-option
                        v-for="file in trainingFiles"
                        :key="file"
                        :label="file"
                        :value="file">
                    </el-option>
                </el-select>
            </el-form-item>
            <el-form-item label="选择测试数据">
                <el-select v-model="testingDataPath" placeholder="请选择测试数据" style="width: 300px;">
                    <el-option
                        v-for="file in testingFiles"
                        :key="file"
                        :label="file"
                        :value="file">
                    </el-option>
                </el-select>
            </el-form-item>
            <el-form-item label="选择训练算法">
                <el-select v-model="selectedAlgorithm" placeholder="请选择算法" style="width: 300px;">
                    <el-option v-for="item in algorithms" :key="item" :label="item" :value="item"></el-option>
                </el-select>
            </el-form-item>            

            <el-form-item label="数据采样频率/Hz">
                <el-input v-model="trainingSampleRate" type="number" placeholder="请输入数据采样频率" style="width: 300px;"></el-input>
            </el-form-item>

            <el-form-item label="训练模型路径及名称">
                <el-input v-model="trainingModelName" placeholder="请输入训练模型路径及名称" style="width: 300px;"></el-input>
            </el-form-item>

            <el-form-item>
                <el-button type="primary" @click="handleTrainingSubmit">开始训练</el-button>
            </el-form-item>
        </div>

        <!-- Training Progress -->
        <div v-if="trainingInProgress">
            <p>训练中...</p>
        </div>

        <!-- Training Result -->
        <div v-if="trainingResult">
            <p>训练结果：{{ trainingResult }}</p>
        </div>

        <!-- Testing Options -->
        <div v-if="showTestOptions">
            <el-form-item label="选择训练数据">
                <el-select v-model="trainingDataPath" placeholder="请选择训练数据" style="width: 300px;">
                    <el-option
                        v-for="file in trainingFiles"
                        :key="file"
                        :label="file"
                        :value="file">
                    </el-option>
                </el-select>
            </el-form-item>
            <el-form-item label="选择测试数据">
                <el-select v-model="testingDataPath" placeholder="请选择测试数据" style="width: 300px;">
                    <el-option
                        v-for="file in testingFiles"
                        :key="file"
                        :label="file"
                        :value="file">
                    </el-option>
                </el-select>
            </el-form-item>
            <el-form-item label="选择测试算法">
                <el-select v-model="selectedAlgorithm" placeholder="请选择算法" style="width: 300px;">
                    <el-option v-for="item in algorithms" :key="item" :label="item" :value="item"></el-option>
                </el-select>
            </el-form-item>

            <el-form-item label="数据采样频率/Hz">
                <el-input v-model="testingSampleRate" type="number" placeholder="请输入数据采样频率" style="width: 300px;"></el-input>
            </el-form-item>

            <el-form-item label="测试模型路径及名称">
                <el-input v-model="testingModelName" placeholder="请输入测试模型路径及名称" style="width: 300px;"></el-input>
            </el-form-item>
            <el-form-item>
                <el-button type="primary" @click="handleTestingSubmit">开始测试</el-button>
            </el-form-item>
        </div>

        <!-- Testing Progress -->
        <div v-if="testingInProgress">
            <p>测试中...</p>
        </div>

        <!-- Testing Result -->
        <div v-if="testingResult">
            <p>测试结果：</p>
            <div class="chart-container">
                <div id="chart" style="width: 100%; height: 400px;"></div>
            </div>
            <div class="table-container">
                <el-table :data="tableData" border>
                    <el-table-column prop="metric" label="指标"></el-table-column>
                    <el-table-column prop="value" label="值"></el-table-column>
                </el-table>
            </div>
        </div>
    </el-form>
</div>
